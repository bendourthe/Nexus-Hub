### Step 4: Navigation

Compose Navigation provides a declarative, type-safe way to manage screen transitions, deep links, and nested navigation graphs.

**Type-Safe Route Definitions**:

```kotlin
import kotlinx.serialization.Serializable

/**
 * Define routes as @Serializable data classes or objects.
 * This approach provides compile-time safety for navigation arguments.
 */
sealed interface Route {
    @Serializable
    data object Home : Route

    @Serializable
    data object Profile : Route

    @Serializable
    data object Settings : Route

    @Serializable
    data class ArticleDetail(val articleId: String) : Route

    @Serializable
    data class UserProfile(val userId: String, val tab: String = "posts") : Route
}

/**
 * Top-level navigation destinations for bottom navigation.
 */
enum class TopLevelDestination(
    val route: Route,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector,
    val label: String,
) {
    HOME(
        route = Route.Home,
        selectedIcon = Icons.Filled.Home,
        unselectedIcon = Icons.Outlined.Home,
        label = "Home",
    ),
    PROFILE(
        route = Route.Profile,
        selectedIcon = Icons.Filled.Person,
        unselectedIcon = Icons.Outlined.Person,
        label = "Profile",
    ),
    SETTINGS(
        route = Route.Settings,
        selectedIcon = Icons.Filled.Settings,
        unselectedIcon = Icons.Outlined.Settings,
        label = "Settings",
    ),
}
```

**Navigation Host with Bottom Navigation**:

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.toRoute

@Composable
fun MainScreen() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    // Determine whether to show bottom navigation
    val showBottomBar = TopLevelDestination.entries.any { dest ->
        currentDestination?.hasRoute(dest.route::class) == true
    }

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    TopLevelDestination.entries.forEach { destination ->
                        val selected = currentDestination?.hierarchy?.any {
                            it.hasRoute(destination.route::class)
                        } == true

                        NavigationBarItem(
                            selected = selected,
                            onClick = {
                                navController.navigate(destination.route) {
                                    // Pop up to the start destination to avoid
                                    // building up a large back stack
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = {
                                Icon(
                                    imageVector = if (selected) destination.selectedIcon
                                        else destination.unselectedIcon,
                                    contentDescription = destination.label,
                                )
                            },
                            label = { Text(destination.label) },
                        )
                    }
                }
            }
        },
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Route.Home,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable<Route.Home> {
                HomeScreen(
                    onArticleClick = { articleId ->
                        navController.navigate(Route.ArticleDetail(articleId))
                    },
                )
            }

            composable<Route.Profile> {
                ProfileScreen(
                    onUserClick = { userId ->
                        navController.navigate(Route.UserProfile(userId))
                    },
                )
            }

            composable<Route.Settings> {
                SettingsScreen()
            }

            composable<Route.ArticleDetail> { backStackEntry ->
                val route = backStackEntry.toRoute<Route.ArticleDetail>()
                ArticleDetailScreen(articleId = route.articleId)
            }

            composable<Route.UserProfile> { backStackEntry ->
                val route = backStackEntry.toRoute<Route.UserProfile>()
                UserProfileScreen(userId = route.userId, initialTab = route.tab)
            }
        }
    }
}
```

**Deep Links**:

```kotlin
import androidx.navigation.navDeepLink

// Inside the NavHost builder:
composable<Route.ArticleDetail>(
    deepLinks = listOf(
        navDeepLink<Route.ArticleDetail>(
            basePath = "https://myapp.example.com/articles",
        ),
    ),
) { backStackEntry ->
    val route = backStackEntry.toRoute<Route.ArticleDetail>()
    ArticleDetailScreen(articleId = route.articleId)
}
```

**AndroidManifest.xml Deep Link Configuration**:

```xml
<activity android:name=".MainActivity"
    android:exported="true">
    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https"
              android:host="myapp.example.com"
              android:pathPrefix="/articles" />
    </intent-filter>
</activity>
```

**Key Navigation Principles**:

- Define routes as `@Serializable` data classes or objects to get compile-time safety for navigation arguments
- Use `popUpTo` with `saveState = true` and `restoreState = true` on bottom navigation items to preserve each tab's back stack
- Hide the bottom navigation bar on detail screens by checking whether the current destination is a top-level route
- Use `launchSingleTop = true` to prevent duplicate destinations on repeated taps
- Configure deep links both in the `NavHost` and in `AndroidManifest.xml` with `android:autoVerify="true"` for App Links
