### Step 2: Jetpack Compose Fundamentals

Jetpack Compose uses a declarative, function-based approach to UI. Understanding composable functions, state management, recomposition, and Modifier chains is essential for building performant Compose UIs.

**Composable Functions and State Hoisting**:

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Stateful wrapper that owns the search query state.
 * Use this pattern at the screen level, hoisting state up to the
 * nearest common ancestor that needs it.
 */
@Composable
fun SearchScreen(
    onNavigateToResult: (query: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    // rememberSaveable survives configuration changes (rotation, process death)
    var query by rememberSaveable { mutableStateOf("") }
    var isSearching by rememberSaveable { mutableStateOf(false) }

    SearchContent(
        query = query,
        isSearching = isSearching,
        onQueryChange = { query = it },
        onSearch = {
            isSearching = true
            onNavigateToResult(query)
        },
        modifier = modifier,
    )
}

/**
 * Stateless composable that receives all state as parameters.
 * This pattern makes the component testable, previewable, and reusable.
 */
@Composable
fun SearchContent(
    query: String,
    isSearching: Boolean,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        OutlinedTextField(
            value = query,
            onValueChange = onQueryChange,
            label = { Text("Search") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        Button(
            onClick = onSearch,
            enabled = query.isNotBlank() && !isSearching,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (isSearching) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                )
                Spacer(modifier = Modifier.width(8.dp))
            }
            Text(if (isSearching) "Searching..." else "Search")
        }
    }
}
```

**Stable Types and Recomposition Optimization**:

```kotlin
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.Stable

/**
 * Mark data classes as @Immutable when all properties are val and
 * use immutable types. This tells the Compose compiler the class
 * will never change after construction, enabling recomposition skipping.
 */
@Immutable
data class ArticleUiModel(
    val id: String,
    val title: String,
    val summary: String,
    val imageUrl: String?,
    val publishedAt: String,
    val isBookmarked: Boolean,
)

/**
 * Use @Stable for classes where the Compose compiler cannot infer stability
 * (e.g., classes with mutable internal state that is observed correctly).
 */
@Stable
class ArticleListState(
    val articles: List<ArticleUiModel>,
    val isLoading: Boolean,
    val errorMessage: String?,
) {
    companion object {
        val Empty = ArticleListState(
            articles = emptyList(),
            isLoading = false,
            errorMessage = null,
        )
    }
}

/**
 * Use derivedStateOf to avoid unnecessary recompositions when the derived
 * value has not actually changed, even if the source state has.
 */
@Composable
fun ArticleList(
    articles: List<ArticleUiModel>,
    modifier: Modifier = Modifier,
) {
    // Only recomposes when the count actually changes, not on every list update
    val bookmarkCount by remember(articles) {
        derivedStateOf { articles.count { it.isBookmarked } }
    }

    Column(modifier = modifier) {
        Text(
            text = "$bookmarkCount bookmarked",
            style = MaterialTheme.typography.labelMedium,
        )
        // Use key() to help Compose identify items across recompositions
        articles.forEach { article ->
            key(article.id) {
                ArticleCard(article = article)
            }
        }
    }
}
```

**Modifier Chain Best Practices**:

```kotlin
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

/**
 * Modifier order matters. Each modifier wraps the previous one.
 * Common pattern: size/padding -> shape/clip -> background -> content padding -> interaction.
 */
@Composable
fun ArticleCard(
    article: ArticleUiModel,
    onClick: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier
            // 1. External spacing (caller controls placement)
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp)
            // 2. Shadow before clip so it renders outside the shape
            .shadow(elevation = 2.dp, shape = RoundedCornerShape(12.dp))
            // 3. Clip to shape for rounded corners on ripple and content
            .clip(RoundedCornerShape(12.dp))
            // 4. Clickable after clip so the ripple respects the shape
            .clickable(onClick = onClick)
            // 5. Accessibility: provide a content description for screen readers
            .semantics {
                contentDescription = "Article: ${article.title}"
            },
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = article.title,
                style = MaterialTheme.typography.titleMedium,
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = article.summary,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 3,
            )
        }
    }
}
```

**Compose Previews**:

```kotlin
import androidx.compose.material3.Surface
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.tooling.preview.PreviewParameter
import androidx.compose.ui.tooling.preview.PreviewParameterProvider

class ArticlePreviewProvider : PreviewParameterProvider<ArticleUiModel> {
    override val values: Sequence<ArticleUiModel> = sequenceOf(
        ArticleUiModel(
            id = "1",
            title = "Jetpack Compose Best Practices",
            summary = "Learn how to build performant UIs with Compose...",
            imageUrl = null,
            publishedAt = "2024-12-01",
            isBookmarked = false,
        ),
        ArticleUiModel(
            id = "2",
            title = "A Very Long Title That Should Wrap to Multiple Lines in the Card Layout",
            summary = "Short summary.",
            imageUrl = "https://example.com/image.jpg",
            publishedAt = "2024-11-15",
            isBookmarked = true,
        ),
    )
}

@Preview(showBackground = true, name = "Light Mode")
@Preview(showBackground = true, name = "Dark Mode",
    uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun ArticleCardPreview(
    @PreviewParameter(ArticlePreviewProvider::class) article: ArticleUiModel,
) {
    MyAppTheme {
        Surface {
            ArticleCard(article = article, onClick = {})
        }
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 640)
@Composable
private fun SearchScreenPreview() {
    MyAppTheme {
        SearchContent(
            query = "Kotlin",
            isSearching = false,
            onQueryChange = {},
            onSearch = {},
        )
    }
}
```

**Key Compose Principles**:

- Hoist state to the lowest common ancestor that needs it. Stateless composables are easier to test and preview
- Use `rememberSaveable` for state that must survive configuration changes; use `remember` for transient UI state only
- Mark data classes with `@Immutable` or `@Stable` to help the Compose compiler skip unnecessary recompositions
- Always accept a `modifier: Modifier = Modifier` parameter as the last optional parameter on public composables
- Use `derivedStateOf` when computing a value from other state objects to avoid redundant recompositions
- Modifier order matters: size and padding modifiers wrap outer to inner, and clickable should come after clip for correct ripple bounds
