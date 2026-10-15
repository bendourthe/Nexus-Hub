### Step 6: Data Layer

The data layer manages data from local (Room, DataStore) and remote (Retrofit, Ktor) sources. An offline-first approach serves cached data immediately while fetching updates in the background.

**Room Database**:

```kotlin
import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "articles")
data class ArticleEntity(
    @PrimaryKey
    val id: String,
    val title: String,
    val summary: String,
    @ColumnInfo(name = "image_url")
    val imageUrl: String?,
    @ColumnInfo(name = "published_at")
    val publishedAt: Long,
    @ColumnInfo(name = "is_bookmarked")
    val isBookmarked: Boolean = false,
    @ColumnInfo(name = "last_fetched_at")
    val lastFetchedAt: Long = System.currentTimeMillis(),
)

@Dao
interface ArticleDao {
    @Query("SELECT * FROM articles ORDER BY published_at DESC")
    fun observeAll(): Flow<List<ArticleEntity>>

    @Query("SELECT * FROM articles WHERE id = :id")
    suspend fun getById(id: String): ArticleEntity?

    @Upsert
    suspend fun upsertAll(articles: List<ArticleEntity>)

    @Query("UPDATE articles SET is_bookmarked = :isBookmarked WHERE id = :id")
    suspend fun updateBookmark(id: String, isBookmarked: Boolean)

    @Query("DELETE FROM articles WHERE last_fetched_at < :cutoff")
    suspend fun deleteStale(cutoff: Long)

    @Query("SELECT COUNT(*) FROM articles")
    suspend fun count(): Int
}

@Database(
    entities = [ArticleEntity::class],
    version = 1,
    exportSchema = true,
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun articleDao(): ArticleDao
}

class Converters {
    @TypeConverter
    fun fromTimestamp(value: Long?): java.util.Date? = value?.let { java.util.Date(it) }

    @TypeConverter
    fun dateToTimestamp(date: java.util.Date?): Long? = date?.time
}
```

**Room Database Migrations**:

```kotlin
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            "ALTER TABLE articles ADD COLUMN author_name TEXT DEFAULT NULL",
        )
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE IF NOT EXISTS article_tags (
                article_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY(article_id, tag),
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
            )""",
        )
        db.execSQL(
            "CREATE INDEX index_article_tags_tag ON article_tags(tag)",
        )
    }
}
```

**DataStore for Preferences**:

```kotlin
import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(
    name = "user_preferences",
)

data class UserPreferences(
    val darkMode: DarkMode = DarkMode.SYSTEM,
    val dynamicColor: Boolean = true,
    val notificationsEnabled: Boolean = true,
    val articlesPerPage: Int = 20,
)

enum class DarkMode { LIGHT, DARK, SYSTEM }

@Singleton
class UserPreferencesRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private object Keys {
        val DARK_MODE = stringPreferencesKey("dark_mode")
        val DYNAMIC_COLOR = booleanPreferencesKey("dynamic_color")
        val NOTIFICATIONS = booleanPreferencesKey("notifications_enabled")
        val ARTICLES_PER_PAGE = intPreferencesKey("articles_per_page")
    }

    val preferences: Flow<UserPreferences> = context.dataStore.data
        .catch { exception ->
            if (exception is IOException) {
                emit(emptyPreferences())
            } else {
                throw exception
            }
        }
        .map { prefs ->
            UserPreferences(
                darkMode = prefs[Keys.DARK_MODE]?.let {
                    DarkMode.valueOf(it)
                } ?: DarkMode.SYSTEM,
                dynamicColor = prefs[Keys.DYNAMIC_COLOR] ?: true,
                notificationsEnabled = prefs[Keys.NOTIFICATIONS] ?: true,
                articlesPerPage = prefs[Keys.ARTICLES_PER_PAGE] ?: 20,
            )
        }

    suspend fun setDarkMode(mode: DarkMode) {
        context.dataStore.edit { it[Keys.DARK_MODE] = mode.name }
    }

    suspend fun setDynamicColor(enabled: Boolean) {
        context.dataStore.edit { it[Keys.DYNAMIC_COLOR] = enabled }
    }

    suspend fun setNotificationsEnabled(enabled: Boolean) {
        context.dataStore.edit { it[Keys.NOTIFICATIONS] = enabled }
    }
}
```

**Retrofit Networking**:

```kotlin
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import retrofit2.http.*

@Serializable
data class ArticleDto(
    val id: String,
    val title: String,
    val summary: String,
    @SerialName("image_url")
    val imageUrl: String?,
    @SerialName("published_at")
    val publishedAt: String,
    @SerialName("author_name")
    val authorName: String?,
)

@Serializable
data class ArticleListResponse(
    val articles: List<ArticleDto>,
    @SerialName("total_count")
    val totalCount: Int,
    @SerialName("next_cursor")
    val nextCursor: String?,
)

interface ArticleApi {
    @GET("v1/articles")
    suspend fun getArticles(
        @Query("cursor") cursor: String? = null,
        @Query("limit") limit: Int = 20,
    ): ArticleListResponse

    @GET("v1/articles/{id}")
    suspend fun getArticle(@Path("id") id: String): ArticleDto

    @POST("v1/articles/{id}/bookmark")
    suspend fun bookmark(@Path("id") id: String)

    @DELETE("v1/articles/{id}/bookmark")
    suspend fun removeBookmark(@Path("id") id: String)
}
```

**Offline-First Repository Implementation**:

```kotlin
import kotlinx.coroutines.flow.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ArticleRepositoryImpl @Inject constructor(
    private val articleApi: ArticleApi,
    private val articleDao: ArticleDao,
) : ArticleRepository {

    /**
     * Offline-first: emit cached data immediately, then fetch fresh data
     * from the network and update the cache. The Flow automatically
     * re-emits when the Room database is updated.
     */
    override fun getArticles(): Flow<List<Article>> {
        return articleDao.observeAll()
            .map { entities -> entities.map { it.toDomain() } }
            .onStart {
                // Trigger a background refresh; errors are logged, not propagated
                try {
                    refreshArticles()
                } catch (e: Exception) {
                    // Log but do not interrupt the cached data flow
                    timber.log.Timber.w(e, "Failed to refresh articles from network")
                }
            }
    }

    override suspend fun getArticleById(id: String): Article? {
        return articleDao.getById(id)?.toDomain()
    }

    override suspend fun updateBookmark(id: String, isBookmarked: Boolean) {
        // Optimistic update: update local first, then sync to server
        articleDao.updateBookmark(id, isBookmarked)
        try {
            if (isBookmarked) articleApi.bookmark(id)
            else articleApi.removeBookmark(id)
        } catch (e: Exception) {
            // Rollback local change on network failure
            articleDao.updateBookmark(id, !isBookmarked)
            throw e
        }
    }

    override suspend fun refreshArticles() {
        val response = articleApi.getArticles()
        val entities = response.articles.map { dto ->
            ArticleEntity(
                id = dto.id,
                title = dto.title,
                summary = dto.summary,
                imageUrl = dto.imageUrl,
                publishedAt = java.time.Instant.parse(dto.publishedAt).toEpochMilli(),
                lastFetchedAt = System.currentTimeMillis(),
            )
        }
        articleDao.upsertAll(entities)
        // Clean up articles not refreshed in the last 7 days
        val cutoff = System.currentTimeMillis() - 7 * 24 * 60 * 60 * 1000L
        articleDao.deleteStale(cutoff)
    }
}
```

**Paging 3 Integration**:

```kotlin
import androidx.paging.*
import kotlinx.coroutines.flow.Flow

@OptIn(ExperimentalPagingApi::class)
class ArticlePagingRepository @Inject constructor(
    private val articleApi: ArticleApi,
    private val articleDao: ArticleDao,
    private val database: AppDatabase,
) {
    fun getPagedArticles(): Flow<PagingData<Article>> {
        return Pager(
            config = PagingConfig(
                pageSize = 20,
                prefetchDistance = 5,
                enablePlaceholders = false,
            ),
            remoteMediator = ArticleRemoteMediator(articleApi, articleDao, database),
            pagingSourceFactory = { articleDao.pagingSource() },
        ).flow.map { pagingData ->
            pagingData.map { entity -> entity.toDomain() }
        }
    }
}

@OptIn(ExperimentalPagingApi::class)
class ArticleRemoteMediator(
    private val api: ArticleApi,
    private val dao: ArticleDao,
    private val database: AppDatabase,
) : RemoteMediator<Int, ArticleEntity>() {

    override suspend fun load(
        loadType: LoadType,
        state: PagingState<Int, ArticleEntity>,
    ): MediatorResult {
        val cursor = when (loadType) {
            LoadType.REFRESH -> null
            LoadType.PREPEND -> return MediatorResult.Success(endOfPaginationReached = true)
            LoadType.APPEND -> {
                // Retrieve the next cursor from the last loaded page
                state.lastItemOrNull()?.id ?: return MediatorResult.Success(
                    endOfPaginationReached = true,
                )
            }
        }

        return try {
            val response = api.getArticles(
                cursor = cursor,
                limit = state.config.pageSize,
            )
            val entities = response.articles.map { it.toEntity() }

            database.withTransaction {
                if (loadType == LoadType.REFRESH) {
                    dao.deleteStale(0) // Clear all on refresh
                }
                dao.upsertAll(entities)
            }

            MediatorResult.Success(
                endOfPaginationReached = response.nextCursor == null,
            )
        } catch (e: Exception) {
            MediatorResult.Error(e)
        }
    }
}
```

**Key Data Layer Principles**:

- Use Room's `Flow`-returning queries to observe database changes reactively. Updates from network refreshes automatically trigger UI updates through the Flow chain
- Prefer `@Upsert` over `@Insert(onConflict = REPLACE)` for batch updates, as Upsert is more efficient and explicit
- Use DataStore for key-value preferences (replacing SharedPreferences). Use Proto DataStore for complex structured data
- Implement optimistic updates for user actions (bookmarks, likes) by updating the local database first, then syncing to the server with rollback on failure
- Use Paging 3 with `RemoteMediator` for large datasets that combine local caching with network pagination
- Always define database migrations for schema changes; never use `fallbackToDestructiveMigration()` in production
