### Step 5: Architecture Patterns

Modern Android architecture follows a unidirectional data flow pattern with clear separation between UI, domain, and data layers. ViewModel exposes UI state, the domain layer contains business logic, and the data layer manages data sources.

**UiState and ViewModel**:

```kotlin
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Sealed interface for UI state. Each subtype represents a distinct
 * state the screen can be in. Prefer a single sealed hierarchy over
 * multiple boolean flags to make impossible states unrepresentable.
 */
sealed interface ArticleListUiState {
    data object Loading : ArticleListUiState

    data class Success(
        val articles: List<ArticleUiModel>,
        val isRefreshing: Boolean = false,
    ) : ArticleListUiState

    data class Error(
        val message: String,
        val canRetry: Boolean = true,
    ) : ArticleListUiState
}

/**
 * One-shot events that the UI should handle exactly once (navigation,
 * snackbar, etc.). Use a Channel or SharedFlow, not StateFlow.
 */
sealed interface ArticleListEvent {
    data class ShowSnackbar(val message: String) : ArticleListEvent
    data class NavigateToDetail(val articleId: String) : ArticleListEvent
}

/**
 * User actions that the UI sends to the ViewModel.
 */
sealed interface ArticleListAction {
    data object LoadArticles : ArticleListAction
    data object Refresh : ArticleListAction
    data class ToggleBookmark(val articleId: String) : ArticleListAction
    data class ArticleClicked(val articleId: String) : ArticleListAction
}

@HiltViewModel
class ArticleListViewModel @Inject constructor(
    private val getArticlesUseCase: GetArticlesUseCase,
    private val toggleBookmarkUseCase: ToggleBookmarkUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow<ArticleListUiState>(ArticleListUiState.Loading)
    val uiState: StateFlow<ArticleListUiState> = _uiState.asStateFlow()

    private val _events = MutableSharedFlow<ArticleListEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<ArticleListEvent> = _events.asSharedFlow()

    init {
        onAction(ArticleListAction.LoadArticles)
    }

    fun onAction(action: ArticleListAction) {
        when (action) {
            is ArticleListAction.LoadArticles -> loadArticles()
            is ArticleListAction.Refresh -> refresh()
            is ArticleListAction.ToggleBookmark -> toggleBookmark(action.articleId)
            is ArticleListAction.ArticleClicked -> {
                _events.tryEmit(ArticleListEvent.NavigateToDetail(action.articleId))
            }
        }
    }

    private fun loadArticles() {
        viewModelScope.launch {
            _uiState.value = ArticleListUiState.Loading
            getArticlesUseCase()
                .catch { e ->
                    _uiState.value = ArticleListUiState.Error(
                        message = e.message ?: "Failed to load articles",
                    )
                }
                .collect { articles ->
                    _uiState.value = ArticleListUiState.Success(
                        articles = articles.map { it.toUiModel() },
                    )
                }
        }
    }

    private fun refresh() {
        val currentState = _uiState.value
        if (currentState is ArticleListUiState.Success) {
            _uiState.value = currentState.copy(isRefreshing = true)
        }
        loadArticles()
    }

    private fun toggleBookmark(articleId: String) {
        viewModelScope.launch {
            toggleBookmarkUseCase(articleId)
                .onFailure { e ->
                    _events.tryEmit(
                        ArticleListEvent.ShowSnackbar("Failed to update bookmark"),
                    )
                }
        }
    }
}
```

**Use Cases (Domain Layer)**:

```kotlin
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

/**
 * Use cases encapsulate a single piece of business logic.
 * They depend on repository interfaces (defined in domain),
 * not on concrete implementations (defined in data).
 */
class GetArticlesUseCase @Inject constructor(
    private val articleRepository: ArticleRepository,
) {
    /**
     * Returns a Flow of articles sorted by publication date.
     * The repository handles the offline-first caching strategy.
     */
    operator fun invoke(): Flow<List<Article>> {
        return articleRepository.getArticles()
    }
}

class ToggleBookmarkUseCase @Inject constructor(
    private val articleRepository: ArticleRepository,
) {
    suspend operator fun invoke(articleId: String): Result<Unit> {
        return runCatching {
            val article = articleRepository.getArticleById(articleId)
                ?: throw IllegalArgumentException("Article $articleId not found")
            articleRepository.updateBookmark(articleId, !article.isBookmarked)
        }
    }
}

/**
 * Repository interface defined in the domain layer.
 * The data layer provides the concrete implementation.
 */
interface ArticleRepository {
    fun getArticles(): Flow<List<Article>>
    suspend fun getArticleById(id: String): Article?
    suspend fun updateBookmark(id: String, isBookmarked: Boolean)
    suspend fun refreshArticles()
}
```

**Hilt Dependency Injection**:

```kotlin
import android.app.Application
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.HiltAndroidApp
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@HiltAndroidApp
class MyApplication : Application()

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    @Singleton
    abstract fun bindArticleRepository(
        impl: ArticleRepositoryImpl,
    ): ArticleRepository
}

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(app: Application): AppDatabase {
        return Room.databaseBuilder(
            app,
            AppDatabase::class.java,
            "myapp.db",
        )
            .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
            .build()
    }

    @Provides
    fun provideArticleDao(db: AppDatabase): ArticleDao = db.articleDao()
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY
                    else HttpLoggingInterceptor.Level.NONE
            })
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(client: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://api.example.com/")
            .client(client)
            .addConverterFactory(
                Json.asConverterFactory("application/json".toMediaType()),
            )
            .build()
    }

    @Provides
    @Singleton
    fun provideArticleApi(retrofit: Retrofit): ArticleApi {
        return retrofit.create(ArticleApi::class.java)
    }
}
```

**Connecting ViewModel to Compose UI**:

```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun ArticleListRoute(
    onNavigateToDetail: (String) -> Unit,
    viewModel: ArticleListViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // Collect one-shot events
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is ArticleListEvent.NavigateToDetail -> {
                    onNavigateToDetail(event.articleId)
                }
                is ArticleListEvent.ShowSnackbar -> {
                    // Show snackbar via SnackbarHostState
                }
            }
        }
    }

    ArticleListScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
    )
}
```

**Key Architecture Principles**:

- Use a sealed interface for UiState to make impossible states unrepresentable (a screen cannot be both loading and showing an error)
- One-shot events (navigation, snackbar) should use `SharedFlow` or `Channel`, not `StateFlow`, to ensure they are consumed exactly once
- Define repository interfaces in the domain layer and implementations in the data layer for testability and inversion of control
- Use `collectAsStateWithLifecycle()` (not `collectAsState()`) to automatically stop collection when the lifecycle is below the minimum active state
- ViewModels should never reference Android framework classes (Context, Activity) directly; use Hilt to inject dependencies instead
