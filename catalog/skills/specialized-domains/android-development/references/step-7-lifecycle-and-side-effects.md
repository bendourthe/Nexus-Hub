### Step 7: Lifecycle and Side Effects

Android lifecycle management is critical for avoiding memory leaks, ensuring correct coroutine scoping, and performing background work reliably.

**LaunchedEffect and Lifecycle-Aware Collection**:

```kotlin
import androidx.compose.runtime.*
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.flow.Flow

/**
 * LaunchedEffect runs a suspend block when the composable enters
 * the composition. It cancels and relaunches when its key changes.
 */
@Composable
fun ArticleDetailScreen(
    articleId: String,
    viewModel: ArticleDetailViewModel = hiltViewModel(),
) {
    // Re-fetch when the articleId changes
    LaunchedEffect(articleId) {
        viewModel.loadArticle(articleId)
    }

    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // Collect one-shot events with lifecycle awareness
    val lifecycleOwner = LocalLifecycleOwner.current
    LaunchedEffect(lifecycleOwner) {
        lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.events.collect { event ->
                when (event) {
                    is ArticleDetailEvent.ShareArticle -> {
                        // Trigger share intent
                    }
                    is ArticleDetailEvent.OpenInBrowser -> {
                        // Open URL
                    }
                }
            }
        }
    }

    ArticleDetailContent(uiState = uiState)
}
```

**DisposableEffect for Cleanup**:

```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.platform.LocalContext

/**
 * DisposableEffect runs setup code when entering composition and
 * cleanup code via onDispose when leaving composition.
 * Use for registering/unregistering listeners, sensors, or callbacks.
 */
@Composable
fun LocationTracker(
    onLocationUpdate: (latitude: Double, longitude: Double) -> Unit,
) {
    val context = LocalContext.current

    DisposableEffect(context) {
        val locationManager = context.getSystemService(
            Context.LOCATION_SERVICE,
        ) as LocationManager

        val listener = object : LocationListener {
            override fun onLocationChanged(location: Location) {
                onLocationUpdate(location.latitude, location.longitude)
            }
        }

        try {
            locationManager.requestLocationUpdates(
                LocationManager.FUSED_PROVIDER,
                5000L,    // minimum time interval (ms)
                10f,      // minimum distance (meters)
                listener,
            )
        } catch (e: SecurityException) {
            // Permission not granted; handle gracefully
        }

        onDispose {
            locationManager.removeUpdates(listener)
        }
    }
}

/**
 * Lifecycle-aware analytics tracking.
 */
@Composable
fun ScreenTracker(screenName: String) {
    val lifecycleOwner = LocalLifecycleOwner.current

    DisposableEffect(lifecycleOwner, screenName) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> {
                    Analytics.trackScreenView(screenName)
                }
                Lifecycle.Event.ON_PAUSE -> {
                    Analytics.trackScreenExit(screenName)
                }
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }
}
```

**WorkManager for Background Tasks**:

```kotlin
import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.*
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.util.concurrent.TimeUnit

@HiltWorker
class ArticleSyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val articleRepository: ArticleRepository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            articleRepository.refreshArticles()
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Result.failure(
                    workDataOf("error" to e.message),
                )
            }
        }
    }

    companion object {
        const val WORK_NAME = "article_sync"

        fun buildPeriodicRequest(): PeriodicWorkRequest {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            return PeriodicWorkRequestBuilder<ArticleSyncWorker>(
                repeatInterval = 6,
                repeatIntervalTimeUnit = TimeUnit.HOURS,
                flexInterval = 30,
                flexTimeUnit = TimeUnit.MINUTES,
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS,
                )
                .addTag("sync")
                .build()
        }

        fun buildOneTimeRequest(): OneTimeWorkRequest {
            return OneTimeWorkRequestBuilder<ArticleSyncWorker>()
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build(),
                )
                .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)
                .build()
        }
    }
}

/**
 * Schedule the sync worker from the Application class or a ViewModel.
 */
fun schedulePeriodicSync(context: Context) {
    WorkManager.getInstance(context).enqueueUniquePeriodicWork(
        ArticleSyncWorker.WORK_NAME,
        ExistingPeriodicWorkPolicy.KEEP,
        ArticleSyncWorker.buildPeriodicRequest(),
    )
}
```

**Foreground Service for Long-Running Operations**:

```kotlin
import android.app.*
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.*
import javax.inject.Inject

@AndroidEntryPoint
class FileUploadService : Service() {

    @Inject
    lateinit var uploadRepository: UploadRepository

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val fileUri = intent?.getStringExtra("file_uri")
            ?: return START_NOT_STICKY

        val notification = createNotification("Uploading file...")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC,
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        serviceScope.launch {
            try {
                uploadRepository.uploadFile(fileUri) { progress ->
                    updateNotification("Uploading: ${progress}%")
                }
                updateNotification("Upload complete")
            } catch (e: Exception) {
                updateNotification("Upload failed: ${e.message}")
            } finally {
                delay(2000) // Brief pause to show final status
                stopSelf()
            }
        }

        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
    }

    private fun createNotification(text: String): Notification {
        createNotificationChannel()
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("File Upload")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_upload)
            .setOngoing(true)
            .setProgress(100, 0, true)
            .build()
    }

    private fun updateNotification(text: String) {
        val notification = createNotification(text)
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, notification)
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "File Uploads",
            NotificationManager.IMPORTANCE_LOW,
        )
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    companion object {
        private const val CHANNEL_ID = "file_upload_channel"
        private const val NOTIFICATION_ID = 1001
    }
}
```

**Key Lifecycle and Side Effect Principles**:

- Use `LaunchedEffect(key)` for suspend operations that should restart when the key changes. Use `LaunchedEffect(Unit)` for one-time setup that runs once per composition
- Use `DisposableEffect` for operations that require explicit cleanup (listeners, sensors, observers)
- Always collect Flows with `collectAsStateWithLifecycle()` in Compose to stop collection when the app is in the background, saving battery and avoiding stale updates
- Use `repeatOnLifecycle(Lifecycle.State.STARTED)` when collecting events in `LaunchedEffect` to ensure proper lifecycle-aware collection
- Prefer WorkManager over foreground services for deferrable background work. WorkManager handles constraints, retries, and backoff automatically
- Declare foreground service types in `AndroidManifest.xml` (required on Android 14+) and request the `FOREGROUND_SERVICE_*` permissions
