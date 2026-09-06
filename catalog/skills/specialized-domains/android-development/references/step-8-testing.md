### Step 8: Testing

Comprehensive Android testing spans unit tests for ViewModels and use cases, Compose UI tests for screen behavior, and integration tests for the data layer.

**ViewModel Unit Tests with JUnit 5 and Turbine**:

```kotlin
import app.cash.turbine.test
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Nested
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith

@OptIn(ExperimentalCoroutinesApi::class)
@ExtendWith(MainDispatcherExtension::class)
class ArticleListViewModelTest {

    private lateinit var getArticlesUseCase: FakeGetArticlesUseCase
    private lateinit var toggleBookmarkUseCase: FakeToggleBookmarkUseCase
    private lateinit var viewModel: ArticleListViewModel

    @BeforeEach
    fun setup() {
        getArticlesUseCase = FakeGetArticlesUseCase()
        toggleBookmarkUseCase = FakeToggleBookmarkUseCase()
        viewModel = ArticleListViewModel(getArticlesUseCase, toggleBookmarkUseCase)
    }

    @Nested
    @DisplayName("Loading articles")
    inner class LoadArticles {

        @Test
        fun `emits Loading then Success when articles are available`() = runTest {
            val articles = listOf(
                testArticle(id = "1", title = "First Article"),
                testArticle(id = "2", title = "Second Article"),
            )
            getArticlesUseCase.setArticles(articles)

            viewModel.uiState.test {
                // Init triggers LoadArticles, first emission is Loading
                assertThat(awaitItem()).isInstanceOf(ArticleListUiState.Loading::class.java)

                val success = awaitItem() as ArticleListUiState.Success
                assertThat(success.articles).hasSize(2)
                assertThat(success.articles[0].title).isEqualTo("First Article")
            }
        }

        @Test
        fun `emits Error when loading fails`() = runTest {
            getArticlesUseCase.setShouldFail(true)

            viewModel.uiState.test {
                assertThat(awaitItem()).isInstanceOf(ArticleListUiState.Loading::class.java)

                val error = awaitItem() as ArticleListUiState.Error
                assertThat(error.message).contains("Failed")
                assertThat(error.canRetry).isTrue()
            }
        }
    }

    @Nested
    @DisplayName("Bookmarking")
    inner class Bookmarking {

        @Test
        fun `emits snackbar event when bookmark toggle fails`() = runTest {
            toggleBookmarkUseCase.setShouldFail(true)

            viewModel.events.test {
                viewModel.onAction(ArticleListAction.ToggleBookmark("1"))

                val event = awaitItem() as ArticleListEvent.ShowSnackbar
                assertThat(event.message).contains("bookmark")
            }
        }
    }

    @Nested
    @DisplayName("Navigation")
    inner class Navigation {

        @Test
        fun `emits navigate event when article is clicked`() = runTest {
            viewModel.events.test {
                viewModel.onAction(ArticleListAction.ArticleClicked("article-42"))

                val event = awaitItem() as ArticleListEvent.NavigateToDetail
                assertThat(event.articleId).isEqualTo("article-42")
            }
        }
    }
}

/**
 * JUnit 5 extension to replace Dispatchers.Main with a test dispatcher.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MainDispatcherExtension : org.junit.jupiter.api.extension.BeforeEachCallback,
    org.junit.jupiter.api.extension.AfterEachCallback {

    private val testDispatcher = UnconfinedTestDispatcher()

    override fun beforeEach(context: org.junit.jupiter.api.extension.ExtensionContext?) {
        Dispatchers.setMain(testDispatcher)
    }

    override fun afterEach(context: org.junit.jupiter.api.extension.ExtensionContext?) {
        Dispatchers.resetMain()
    }
}
```

**Fake Implementations for Testing**:

```kotlin
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flow

class FakeGetArticlesUseCase : GetArticlesUseCase(
    articleRepository = FakeArticleRepository(),
) {
    private var articles: List<Article> = emptyList()
    private var shouldFail = false

    fun setArticles(articles: List<Article>) {
        this.articles = articles
    }

    fun setShouldFail(fail: Boolean) {
        shouldFail = fail
    }

    override operator fun invoke(): Flow<List<Article>> = flow {
        if (shouldFail) {
            throw RuntimeException("Failed to load articles")
        }
        emit(articles)
    }
}

class FakeToggleBookmarkUseCase : ToggleBookmarkUseCase(
    articleRepository = FakeArticleRepository(),
) {
    private var shouldFail = false

    fun setShouldFail(fail: Boolean) {
        shouldFail = fail
    }

    override suspend operator fun invoke(articleId: String): Result<Unit> {
        return if (shouldFail) {
            Result.failure(RuntimeException("Bookmark failed"))
        } else {
            Result.success(Unit)
        }
    }
}

fun testArticle(
    id: String = "test-id",
    title: String = "Test Article",
    summary: String = "Test summary",
    isBookmarked: Boolean = false,
) = Article(
    id = id,
    title = title,
    summary = summary,
    imageUrl = null,
    publishedAt = java.time.Instant.now(),
    isBookmarked = isBookmarked,
)
```

**Compose UI Tests**:

```kotlin
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.junit.Test

class SearchContentTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun searchButton_isDisabled_whenQueryIsBlank() {
        composeTestRule.setContent {
            MyAppTheme {
                SearchContent(
                    query = "",
                    isSearching = false,
                    onQueryChange = {},
                    onSearch = {},
                )
            }
        }

        composeTestRule
            .onNodeWithText("Search")
            .assertIsNotEnabled()
    }

    @Test
    fun searchButton_isEnabled_whenQueryIsNotBlank() {
        composeTestRule.setContent {
            MyAppTheme {
                SearchContent(
                    query = "Kotlin",
                    isSearching = false,
                    onQueryChange = {},
                    onSearch = {},
                )
            }
        }

        composeTestRule
            .onNodeWithText("Search")
            .assertIsEnabled()
    }

    @Test
    fun searchButton_showsProgressIndicator_whenSearching() {
        composeTestRule.setContent {
            MyAppTheme {
                SearchContent(
                    query = "Kotlin",
                    isSearching = true,
                    onQueryChange = {},
                    onSearch = {},
                )
            }
        }

        composeTestRule
            .onNodeWithText("Searching...")
            .assertExists()

        composeTestRule
            .onNodeWithText("Searching...")
            .assertIsNotEnabled()
    }

    @Test
    fun textField_callsOnQueryChange_whenUserTypes() {
        var capturedQuery = ""
        composeTestRule.setContent {
            MyAppTheme {
                SearchContent(
                    query = "",
                    isSearching = false,
                    onQueryChange = { capturedQuery = it },
                    onSearch = {},
                )
            }
        }

        composeTestRule
            .onNodeWithText("Search", useUnmergedTree = true)
            // Find the text field by its label
            .onSiblings()
            .filterToOne(hasSetTextAction())
            .performTextInput("Android")

        assertThat(capturedQuery).isEqualTo("Android")
    }
}

class ArticleCardTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun articleCard_displaysTitle_andSummary() {
        val article = ArticleUiModel(
            id = "1",
            title = "Compose Testing",
            summary = "Learn to test Compose UIs",
            imageUrl = null,
            publishedAt = "2024-12-01",
            isBookmarked = false,
        )

        composeTestRule.setContent {
            MyAppTheme {
                ArticleCard(article = article)
            }
        }

        composeTestRule
            .onNodeWithText("Compose Testing")
            .assertIsDisplayed()

        composeTestRule
            .onNodeWithText("Learn to test Compose UIs")
            .assertIsDisplayed()
    }

    @Test
    fun articleCard_hasCorrectContentDescription() {
        val article = ArticleUiModel(
            id = "1",
            title = "Accessibility Test",
            summary = "Testing a11y",
            imageUrl = null,
            publishedAt = "2024-12-01",
            isBookmarked = false,
        )

        composeTestRule.setContent {
            MyAppTheme {
                ArticleCard(article = article)
            }
        }

        composeTestRule
            .onNodeWithContentDescription("Article: Accessibility Test")
            .assertExists()
    }
}
```

**Room Database Testing with Robolectric**:

```kotlin
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.robolectric.RobolectricTestRunner

@ExtendWith(RobolectricTestRunner::class)
class ArticleDaoTest {

    private lateinit var database: AppDatabase
    private lateinit var dao: ArticleDao

    @BeforeEach
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java,
        )
            .allowMainThreadQueries()
            .build()
        dao = database.articleDao()
    }

    @AfterEach
    fun teardown() {
        database.close()
    }

    @Test
    fun upsertAll_insertsNewArticles() = runTest {
        val articles = listOf(
            ArticleEntity(
                id = "1",
                title = "First",
                summary = "Summary 1",
                imageUrl = null,
                publishedAt = 1000L,
            ),
            ArticleEntity(
                id = "2",
                title = "Second",
                summary = "Summary 2",
                imageUrl = null,
                publishedAt = 2000L,
            ),
        )

        dao.upsertAll(articles)
        val result = dao.observeAll().first()

        assertThat(result).hasSize(2)
        // Ordered by published_at DESC
        assertThat(result[0].title).isEqualTo("Second")
        assertThat(result[1].title).isEqualTo("First")
    }

    @Test
    fun updateBookmark_togglesBookmarkFlag() = runTest {
        dao.upsertAll(listOf(
            ArticleEntity(
                id = "1",
                title = "Test",
                summary = "Summary",
                imageUrl = null,
                publishedAt = 1000L,
                isBookmarked = false,
            ),
        ))

        dao.updateBookmark("1", true)
        val article = dao.getById("1")

        assertThat(article).isNotNull()
        assertThat(article!!.isBookmarked).isTrue()
    }

    @Test
    fun deleteStale_removesOldArticles() = runTest {
        val now = System.currentTimeMillis()
        dao.upsertAll(listOf(
            ArticleEntity(
                id = "fresh",
                title = "Fresh",
                summary = "s",
                imageUrl = null,
                publishedAt = now,
                lastFetchedAt = now,
            ),
            ArticleEntity(
                id = "stale",
                title = "Stale",
                summary = "s",
                imageUrl = null,
                publishedAt = now - 86400000L * 10,
                lastFetchedAt = now - 86400000L * 10,
            ),
        ))

        dao.deleteStale(now - 86400000L * 7)
        val result = dao.observeAll().first()

        assertThat(result).hasSize(1)
        assertThat(result[0].id).isEqualTo("fresh")
    }
}
```

**Hilt Testing**:

```kotlin
import dagger.hilt.android.testing.HiltAndroidRule
import dagger.hilt.android.testing.HiltAndroidTest
import dagger.hilt.android.testing.HiltTestApplication
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import javax.inject.Inject

/**
 * Custom test runner that uses HiltTestApplication.
 */
class HiltTestRunner : AndroidJUnitRunner() {
    override fun newApplication(
        cl: ClassLoader?,
        className: String?,
        context: android.content.Context?,
    ): Application {
        return super.newApplication(cl, HiltTestApplication::class.java.name, context)
    }
}

@HiltAndroidTest
@RunWith(RobolectricTestRunner::class)
@Config(application = HiltTestApplication::class)
class ArticleRepositoryIntegrationTest {

    @get:Rule
    val hiltRule = HiltAndroidRule(this)

    @Inject
    lateinit var articleRepository: ArticleRepository

    @Before
    fun setup() {
        hiltRule.inject()
    }

    @Test
    fun repository_returnsArticles_afterRefresh() = runTest {
        articleRepository.refreshArticles()
        val articles = articleRepository.getArticles().first()
        assertThat(articles).isNotEmpty()
    }
}
```

**Key Testing Principles**:

- Use JUnit 5 with `@Nested` classes to organize tests by behavior. Use `@DisplayName` for human-readable test descriptions
- Use Turbine (`test {}`) for testing Kotlin Flows. It provides `awaitItem()`, `awaitError()`, and `awaitComplete()` for asserting emissions
- Create a `MainDispatcherExtension` (JUnit 5) or `MainDispatcherRule` (JUnit 4) to replace `Dispatchers.Main` with a test dispatcher in ViewModel tests
- Prefer fake implementations over mocks for repositories and use cases. Fakes provide more realistic behavior and are easier to maintain
- Use `createComposeRule()` for Compose UI tests. Query elements by text, content description, or test tag rather than by implementation details
- Test Room DAOs with in-memory databases and `allowMainThreadQueries()` for synchronous assertions
- Use Robolectric to run Android-dependent tests on the JVM without an emulator, significantly speeding up the test suite
