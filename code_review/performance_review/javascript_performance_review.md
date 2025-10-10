# JavaScript Performance Review

## Objective
Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues. Provide data-driven optimization recommendations to improve application speed, scalability, and resource efficiency.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/performance_review/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/performance_review/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Performance Profiling

- [ ] CPU profiling completed (Chrome DevTools, Node.js profiler)

- [ ] Memory profiling performed (Chrome DevTools Memory, node --inspect)

- [ ] I/O operations analyzed

- [ ] Hot paths and bottlenecks identified

- [ ] Function-level timing measurements captured

### Algorithm Efficiency

- [ ] Time complexity evaluated (O(n), O(n²), etc.)

- [ ] Space complexity assessed

- [ ] Inefficient loops identified (nested, redundant)

- [ ] Algorithmic improvements documented

- [ ] Data structure choices reviewed

### Bundle & Asset Performance

- [ ] Bundle size analyzed

- [ ] Code splitting evaluated

- [ ] Lazy loading opportunities identified

- [ ] Tree shaking effectiveness checked

- [ ] Asset optimization reviewed (images, fonts, etc.)

### Runtime Performance

- [ ] Rendering performance measured (FPS, paint times)

- [ ] DOM manipulation efficiency evaluated

- [ ] Event handler performance checked

- [ ] Memory leaks detected

- [ ] Garbage collection patterns analyzed

### Network Performance

- [ ] API call latency measured

- [ ] Request waterfall analyzed

- [ ] Caching strategies reviewed

- [ ] Compression and optimization checked

- [ ] CDN usage evaluated

### Async & Concurrency

- [ ] Promise chains optimized

- [ ] Async/await usage evaluated

- [ ] Parallel request opportunities identified

- [ ] Event loop blocking detected

- [ ] Web Workers usage assessed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Performance Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/performance_review"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Review Protocol

Please perform a comprehensive performance review of this JavaScript application following this protocol:

## Phase 1: Performance Profiling Setup

1. **Browser Performance Profiling (Chrome DevTools)**
   ```javascript
   // Record performance profile
   // 1. Open Chrome DevTools (F12)
   // 2. Go to Performance tab
   // 3. Click Record (Ctrl+E)
   // 4. Perform typical user actions
   // 5. Stop recording
   // 6. Analyze flamegraph and call tree

   // Programmatic performance measurement
   performance.mark('operation-start');
   // ... operation code ...
   performance.mark('operation-end');
   performance.measure('operation', 'operation-start', 'operation-end');
   const measure = performance.getEntriesByName('operation')[0];
   console.log(`Operation took ${measure.duration}ms`);
   ```

2. **Node.js Performance Profiling**
   ```bash
   # Built-in Node.js profiler
   node --prof app.js
   node --prof-process isolate-*.log > ${OUTPUT_DIR}/exports/processed.txt

   # Using clinic.js for comprehensive analysis
   npm install -g clinic

   # Doctor - overall health check
   clinic doctor -- node app.js

   # Bubbleprof - async operations visualization
   clinic bubbleprof -- node app.js

   # Flame - CPU profiling
   clinic flame -- node app.js

   # HeapProfiler - memory analysis
   clinic heapprofiler -- node app.js
   ```

3. **Memory Profiling**
   ```javascript
   // Browser: Chrome DevTools > Memory tab
   // - Take heap snapshots before/after operations
   // - Record allocation timeline
   // - Identify detached DOM nodes

   // Node.js: memory usage monitoring
   const used = process.memoryUsage();
   console.log({
     heapUsed: `${Math.round(used.heapUsed / 1024 / 1024)} MB`,
     heapTotal: `${Math.round(used.heapTotal / 1024 / 1024)} MB`,
     external: `${Math.round(used.external / 1024 / 1024)} MB`,
     rss: `${Math.round(used.rss / 1024 / 1024)} MB`
   });
   ```

## Phase 2: Bundle & Asset Analysis

1. **Bundle Size Analysis**
   ```bash
   # Webpack Bundle Analyzer
   npm install --save-dev webpack-bundle-analyzer

   # Add to webpack.config.js
   const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
   module.exports = {
     plugins: [new BundleAnalyzerPlugin()]
   };

   # For Vite
   npm install --save-dev rollup-plugin-visualizer

   # Source Map Explorer
   npm install -g source-map-explorer
   source-map-explorer bundle.js bundle.js.map
   ```

2. **Code Splitting Opportunities**
   ```javascript
   // Dynamic imports for route-based code splitting
   const Dashboard = lazy(() => import('./Dashboard'));

   // Component-level code splitting
   const HeavyComponent = lazy(() => import('./HeavyComponent'));

   // Library splitting (webpack)
   optimization: {
     splitChunks: {
       chunks: 'all',
       cacheGroups: {
         vendors: {
           test: /[\\/]node_modules[\\/]/,
           priority: -10
         }
       }
     }
   }
   ```

3. **Tree Shaking Effectiveness**
   ```javascript
   // Check for:
   - Side-effect free modules (package.json "sideEffects": false)
   - ES6 module usage (import/export vs require)
   - Unused exports detection
   - Dead code elimination
   ```

## Phase 3: Bottleneck Identification

1. **Analyze Profiling Results**
   - Identify functions consuming >5% of total time
   - Find functions called excessive times
   - Locate memory-intensive operations
   - Identify render-blocking operations

2. **Common Performance Anti-Patterns**
   ```javascript
   // 1. Inefficient array operations in loops
   // BAD: O(n²) nested loops
   for (const item1 of array1) {
     for (const item2 of array2) {
       if (item1.id === item2.id) {
         // process
       }
     }
   }
   // GOOD: Use Map for O(n) lookup
   const map = new Map(array2.map(item => [item.id, item]));
   for (const item1 of array1) {
     const item2 = map.get(item1.id);
     if (item2) {
       // process
     }
   }

   // 2. Excessive DOM manipulation
   // BAD: Multiple reflows
   for (const item of items) {
     const div = document.createElement('div');
     div.textContent = item;
     container.appendChild(div); // Reflow on each append
   }
   // GOOD: Single reflow using DocumentFragment
   const fragment = document.createDocumentFragment();
   for (const item of items) {
     const div = document.createElement('div');
     div.textContent = item;
     fragment.appendChild(div);
   }
   container.appendChild(fragment); // Single reflow

   // 3. Memory leaks from event listeners
   // BAD: Event listener not cleaned up
   element.addEventListener('click', handler);
   // GOOD: Cleanup in component unmount
   useEffect(() => {
     element.addEventListener('click', handler);
     return () => element.removeEventListener('click', handler);
   }, []);

   // 4. Inefficient string concatenation
   // BAD: String concatenation in loop
   let html = '';
   for (const item of items) {
     html += `<div>${item}</div>`;
   }
   // GOOD: Array join
   const html = items.map(item => `<div>${item}</div>`).join('');

   // 5. Blocking the event loop
   // BAD: Synchronous heavy computation
   function processLargeArray(items) {
     return items.map(item => expensiveOperation(item));
   }
   // GOOD: Chunk processing or Web Worker
   async function processLargeArray(items) {
     const chunkSize = 1000;
     const results = [];
     for (let i = 0; i < items.length; i += chunkSize) {
       const chunk = items.slice(i, i + chunkSize);
       results.push(...chunk.map(item => expensiveOperation(item)));
       await new Promise(resolve => setTimeout(resolve, 0)); // Yield to event loop
     }
     return results;
   }

   // 6. Unnecessary re-renders (React)
   // BAD: Creating new objects in render
   <Component data={{ items: [] }} /> // New object every render
   // GOOD: Memoize or define outside
   const data = useMemo(() => ({ items: [] }), []);
   <Component data={data} />
   ```

## Phase 4: Network & API Performance

1. **API Call Analysis**
   ```javascript
   // Measure API performance
   console.time('api-call');
   const response = await fetch('/api/data');
   console.timeEnd('api-call');

   // Check for:
   - Sequential API calls that could be parallel
   - Missing request caching
   - Large payload sizes
   - Missing compression
   - Excessive API calls (N+1 problems)
   ```

2. **Network Optimization Patterns**
   ```javascript
   // BAD: Sequential requests
   const user = await fetchUser(userId);
   const posts = await fetchPosts(userId);
   const comments = await fetchComments(userId);

   // GOOD: Parallel requests
   const [user, posts, comments] = await Promise.all([
     fetchUser(userId),
     fetchPosts(userId),
     fetchComments(userId)
   ]);

   // Request deduplication
   const cache = new Map();
   async function fetchWithCache(url) {
     if (cache.has(url)) {
       return cache.get(url);
     }
     const promise = fetch(url).then(r => ${OUTPUT_DIR}/exports/r.json());
     cache.set(url, promise);
     return promise;
   }

   // Request batching
   class RequestBatcher {
     constructor(batchFn, delay = 10) {
       this.batchFn = batchFn;
       this.delay = delay;
       this.queue = [];
       this.timer = null;
     }

     add(item) {
       return new Promise((resolve, reject) => {
         this.queue.push({ item, resolve, reject });
         if (!this.timer) {
           this.timer = setTimeout(() => this.flush(), this.delay);
         }
       });
     }

     flush() {
       const batch = this.queue;
       this.queue = [];
       this.timer = null;
       this.batchFn(batch.map(b => b.item))
         .then(results => {
           batch.forEach((b, i) => b.resolve(results[i]));
         })
         .catch(error => {
           batch.forEach(b => b.reject(error));
         });
     }
   }
   ```

## Phase 5: Rendering Performance

1. **Frame Rate Analysis**
   ```javascript
   // Monitor FPS
   let lastTime = performance.now();
   let frames = 0;

   function measureFPS() {
     frames++;
     const currentTime = performance.now();
     if (currentTime >= lastTime + 1000) {
       console.log(`FPS: ${frames}`);
       frames = 0;
       lastTime = currentTime;
     }
     requestAnimationFrame(measureFPS);
   }
   requestAnimationFrame(measureFPS);

   // Use Chrome DevTools:
   // - Performance tab: record and check for dropped frames
   // - Rendering tab: Enable "Frame Rendering Stats"
   // - Look for long tasks (>50ms)
   ```

2. **React-Specific Performance**
   ```javascript
   // Use React DevTools Profiler
   // 1. Install React DevTools extension
   // 2. Go to Profiler tab
   // 3. Click record, interact, stop
   // 4. Analyze component render times

   // Optimization patterns
   // 1. Memoization
   const MemoizedComponent = React.memo(Component);
   const memoizedValue = useMemo(() => computeExpensive(a, b), [a, b]);
   const memoizedCallback = useCallback(() => doSomething(a, b), [a, b]);

   // 2. Virtualization for long lists
   import { FixedSizeList } from 'react-window';
   <FixedSizeList
     height={600}
     itemCount={items.length}
     itemSize={35}
   >
     {Row}
   </FixedSizeList>

   // 3. Lazy loading
   const LazyComponent = lazy(() => import('./Component'));
   <Suspense fallback={<Loading />}>
     <LazyComponent />
   </Suspense>
   ```

3. **Vue-Specific Performance**
   ```javascript
   // Use Vue DevTools Performance tab

   // Optimization patterns
   // 1. v-once for static content
   <div v-once>{{ staticContent }}</div>

   // 2. v-memo for conditional memoization (Vue 3.2+)
   <Component v-memo="[valueA, valueB]" />

   // 3. Computed vs Methods
   // GOOD: Cached
   computed: {
     filteredItems() {
       return this.items.filter(item => item.active);
     }
   }
   // BAD: Re-computed every render
   methods: {
     filteredItems() {
       return this.items.filter(item => item.active);
     }
   }
   ```

## Phase 6: Memory Management

1. **Memory Leak Detection**
   ```javascript
   // Common memory leak patterns:

   // 1. Forgotten timers/intervals
   // BAD
   setInterval(() => updateData(), 1000);
   // GOOD
   const intervalId = setInterval(() => updateData(), 1000);
   // Later: clearInterval(intervalId);

   // 2. Event listeners not removed
   // BAD
   window.addEventListener('resize', handler);
   // GOOD
   window.addEventListener('resize', handler);
   // Later: window.removeEventListener('resize', handler);

   // 3. Closures holding references
   // BAD
   function createClosure() {
     const largeData = new Array(1000000);
     return function() {
       console.log(largeData[0]);
     };
   }

   // 4. Detached DOM nodes
   // Check with Chrome DevTools Memory > Heap Snapshot
   // Filter by "Detached"
   ```

2. **Heap Analysis**
   ```javascript
   // Chrome DevTools > Memory
   // 1. Take heap snapshot
   // 2. Perform action
   // 3. Take another snapshot
   // 4. Compare snapshots (Comparison view)
   // 5. Look for unexpected growth

   // Node.js heap dump
   const v8 = require('v8');
   const fs = require('fs');

   const heap = v8.writeHeapSnapshot();
   console.log(`Heap snapshot written to ${heap}`);
   ```

## Phase 7: Build & Load Time Optimization

1. **Load Performance**
   ```javascript
   // Lighthouse audit
   npm install -g lighthouse
   lighthouse https://your-app.com --view

   // Core Web Vitals monitoring
   import {getCLS, getFID, getFCP, getLCP, getTTFB} from 'web-vitals';

   getCLS(console.log);  // Cumulative Layout Shift
   getFID(console.log);  // First Input Delay
   getFCP(console.log);  // First Contentful Paint
   getLCP(console.log);  // Largest Contentful Paint
   getTTFB(console.log); // Time to First Byte
   ```

2. **Optimization Strategies**
   ```javascript
   // 1. Preload critical resources
   <link rel="preload" href="critical.js" as="script">
   <link rel="preload" href="font.woff2" as="font" crossorigin>

   // 2. Defer non-critical scripts
   <script defer src="analytics.js"></script>

   // 3. Inline critical CSS
   <style>/* Critical CSS */</style>
   <link rel="preload" href="main.css" as="style" onload="this.rel='stylesheet'">

   // 4. Image optimization
   <img src="image.jpg" loading="lazy" />
   <picture>
     <source srcset="image.webp" type="image/webp">
     <img src="image.jpg" alt="description">
   </picture>
   ```

## Phase 8: Async & Concurrency

1. **Event Loop Monitoring**
   ```javascript
   // Detect event loop blocking
   const startTime = Date.now();
   setTimeout(() => {
     const delay = Date.now() - startTime;
     if (delay > 100) {
       console.warn(`Event loop blocked for ${delay}ms`);
     }
   }, 0);

   // Use performance.now() for precise timing
   const start = performance.now();
   heavyOperation();
   const duration = performance.now() - start;
   if (duration > 50) {
     console.warn(`Long task detected: ${duration}ms`);
   }
   ```

2. **Web Workers for Heavy Computation**
   ```javascript
   // Main thread
   const worker = new Worker('worker.js');
   worker.postMessage({ data: largeDataset });
   worker.onmessage = (e) => {
     console.log('Result:', e.data);
   };

   // worker.js
   self.onmessage = (e) => {
     const result = heavyComputation(e.data.data);
     self.postMessage(result);
   };
   ```

## Phase 9: Database & Backend Performance (Node.js)

1. **Database Query Optimization**
   ```javascript
   // N+1 query problem detection
   // BAD: N+1 queries
   const posts = await Post.findAll();
   for (const post of posts) {
     const author = await User.findByPk(post.authorId); // N queries
   }

   // GOOD: Single query with join
   const posts = await Post.findAll({
     include: [{ model: User, as: 'author' }]
   });

   // Connection pooling
   const pool = new Pool({
     max: 20,
     idleTimeoutMillis: 30000,
     connectionTimeoutMillis: 2000,
   });
   ```

2. **Caching Strategies**
   ```javascript
   // In-memory cache
   const NodeCache = require('node-cache');
   const cache = new NodeCache({ stdTTL: 600 });

   async function getData(key) {
     let data = cache.get(key);
     if (!data) {
       data = await fetchFromDatabase(key);
       cache.set(key, data);
     }
     return data;
   }

   // Redis caching
   const redis = require('redis');
   const client = redis.createClient();

   async function getCachedData(key) {
     const cached = await client.get(key);
     if (cached) return JSON.parse(cached);

     const data = await fetchFromDatabase(key);
     await client.setEx(key, 3600, JSON.stringify(data));
     return data;
   }
   ```

## Phase 10: Load Testing

1. **Load Testing Tools**
   ```bash
   # Autocannon (Node.js HTTP load testing)
   npm install -g autocannon
   autocannon -c 100 -d 30 http://localhost:3000

   # k6 (load testing)
   k6 run load-test.js

   # Artillery
   npm install -g artillery
   artillery quick --count 100 --num 10 http://localhost:3000
   ```

2. **Load Test Script Example**
   ```javascript
   // k6 load test script
   import http from 'k6/http';
   import { check, sleep } from 'k6';

   export const options = {
     stages: [
       { duration: '2m', target: 100 }, // Ramp up
       { duration: '5m', target: 100 }, // Stay at 100 users
       { duration: '2m', target: 200 }, // Ramp up to 200
       { duration: '5m', target: 200 }, // Stay at 200
       { duration: '2m', target: 0 },   // Ramp down
     ],
     thresholds: {
       http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
       http_req_failed: ['rate<0.01'],   // Error rate <1%
     },
   };

   export default function () {
     const res = http.get('http://localhost:3000/api/data');
     check(res, {
       'status is 200': (r) => r.status === 200,
       'response time < 500ms': (r) => r.timings.duration < 500,
     });
     sleep(1);
   }
   ```

## Output Format

Please provide a comprehensive performance report with the following structure:

### Executive Summary

- **Overall Performance**: [Excellent/Good/Fair/Poor]

- **Critical Bottlenecks**: [count and brief description]

- **Performance Impact**: [High/Medium/Low user-facing impact]

- **Optimization Potential**: [percentage improvement possible]

- **Recommended Investment**: [estimated hours for major improvements]

### Performance Profile Overview
**Top 10 Time-Consuming Functions**:
| Function | File | Time | % Total | Calls | Time/Call | Category |
|----------|------|------|---------|-------|-----------|----------|
| [name] | [path] | [ms] | [%] | [count] | [ms] | [CPU/I/O/Render] |

**Top 10 Memory-Consuming Operations**:
| Operation | File:Line | Memory | % Total | Description |
|-----------|-----------|--------|---------|-------------|
| [desc] | [location] | [MB] | [%] | [details] |

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [file:line] | [High] | [metric] | [goal] | [strategy] |

### Bundle Analysis

- **Total Bundle Size**: [KB/MB]

- **Largest Chunks**: [list with sizes]

- **Code Splitting**: [Excellent/Good/Needs improvement]

- **Tree Shaking**: [Effective/Ineffective]

- **Unused Code**: [KB estimated]

**Optimization Opportunities**:
| Library/Module | Current Size | Optimized Size | Method |
|----------------|--------------|----------------|--------|
| [name] | [KB] | [KB] | [dynamic import/replacement/removal] |

### Rendering Performance

- **Average FPS**: [number]

- **Frames Dropped**: [count/percentage]

- **Long Tasks (>50ms)**: [count]

- **Layout Shifts (CLS)**: [score]

**Rendering Issues**:
| Issue | Location | Impact | Fix |
|-------|----------|--------|-----|
| [description] | [component/file] | [High/Med/Low] | [optimization approach] |

### Network Performance

- **API Calls (Avg)**: [count per page/action]

- **Average Latency**: [ms]

- **Slow Endpoints (>500ms)**: [list]

- **Missing Caching**: [opportunities]

- **Bundle Load Time**: [ms]

**Optimization Recommendations**:
1. [Request batching/caching/parallel loading opportunity]
2. [Compression/CDN optimization]

### Memory Analysis

- **Peak Memory Usage**: [MB]

- **Memory Leaks Detected**: [Yes/No - locations if yes]

- **Detached DOM Nodes**: [count]

- **Large Objects**: [list of large allocations]

- **GC Pressure**: [High/Medium/Low]

### Algorithm Inefficiencies
**O(n²) or Worse Algorithms Detected**:
| Function | Location | Complexity | Current Performance | Optimized Approach |
|----------|----------|------------|---------------------|-------------------|
| [name] | [file:line] | [O(n²)] | [metric] | [suggested algorithm] |

### Load Testing Results
**Target Load**: [X concurrent users / Y requests per second]

| Metric | Baseline | Target | Result | Status |
|--------|----------|--------|--------|--------|
| Throughput | [req/s] | [req/s] | - | 🔴 |
| P50 Latency | [ms] | <200ms | - | 🔴 |
| P95 Latency | [ms] | <500ms | - | 🔴 |
| P99 Latency | [ms] | <1000ms | - | 🔴 |
| Error Rate | [%] | <1% | - | 🔴 |

### Core Web Vitals
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| LCP (Largest Contentful Paint) | [s] | <2.5s | 🔴/🟡/🟢 |
| FID (First Input Delay) | [ms] | <100ms | 🔴/🟡/🟢 |
| CLS (Cumulative Layout Shift) | [score] | <0.1 | 🔴/🟡/🟢 |
| FCP (First Contentful Paint) | [s] | <1.8s | 🔴/🟡/🟢 |
| TTFB (Time to First Byte) | [ms] | <600ms | 🔴/🟡/🟢 |

### Optimization Recommendations

**Quick Wins** (< 1 day effort, high impact):
1. **[Optimization]**
   - **Location**: [file:line]
   - **Current**: [metric]
   - **Expected Improvement**: [metric/percentage]
   - **Implementation**: [specific steps]

**Medium-term** (1-3 days effort):
[List of optimizations requiring moderate refactoring]

**Strategic** (> 3 days, architectural changes):
[List of major performance initiatives]

### Framework-Specific Recommendations

**React**:

- Component memoization opportunities: [count]

- Unnecessary re-renders: [locations]

- Virtualization opportunities: [components]

**Vue**:

- Computed vs methods issues: [count]

- v-memo opportunities: [count]

- Unnecessary watchers: [count]

**Angular**:

- Change detection issues: [count]

- OnPush strategy opportunities: [count]

- Pipe optimization: [count]

### Monitoring Recommendations
```javascript
// Implement performance monitoring

- Core Web Vitals tracking

- API latency monitoring (p50, p95, p99)

- Memory usage alerts

- Error rate tracking

- Custom performance marks

// Tools: DataDog, New Relic, Sentry, web-vitals library
```

### Next Steps

- [ ] Implement quick win optimizations

- [ ] Set up performance benchmarking suite

- [ ] Configure production performance monitoring

- [ ] Plan load testing before deployment

- [ ] Schedule performance review sprint

- [ ] Document performance budgets

## Notes

- Optimize based on profiling data, not assumptions

- Focus on user-facing performance improvements first (Core Web Vitals)

- Measure before and after optimization

- Consider bundle size vs runtime performance tradeoffs

- Balance performance with code maintainability

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/performance_review/analysis_scripts
mkdir -p ${OUTPUT_DIR}/performance_review/supporting_data
```

**Save files as follows**:

- Main report → `review/performance_review/performance_review_report.md`

- Findings data → `review/performance_review/performance_review_findings.json`

- Analysis scripts → `review/performance_review/analysis_scripts/`

- Supporting data → `review/performance_review/supporting_data/`
~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
