# Omni JavaScript/TypeScript SDK

Official JavaScript/TypeScript client library for the Omni Enterprise Ultra Max Platform.

## Installation

```bash
# NPM
npm install @omni/client

# Yarn
yarn add @omni/client

# PNPM
pnpm add @omni/client
```

## Quick Start

### TypeScript

```typescript
import { OmniClient } from '@omni/client';

const client = new OmniClient({ apiKey: 'your-api-key-here' });

// Get revenue predictions
const predictions = await client.intelligence.predictRevenue({ userId: 'user123' });
console.log(`Predicted revenue: $${predictions.amount}`);

// Analyze text
const analysis = await client.ai.analyzeText(
  'This product is amazing!',
  'sentiment'
);
console.log(`Sentiment: ${analysis.sentiment}`);

// Get dashboard
const dashboard = await client.analytics.getDashboard();
console.log(`Total users: ${dashboard.total_users}`);
```

### JavaScript (CommonJS)

```javascript
const { OmniClient } = require('@omni/client');

const client = new OmniClient({ apiKey: 'your-api-key-here' });

client.intelligence.predictRevenue({ userId: 'user123' })
  .then(predictions => {
    console.log(`Predicted revenue: $${predictions.amount}`);
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

### Browser (ESM)

```html
<script type="module">
  import { OmniClient } from 'https://cdn.skypack.dev/@omni/client';
  
  const client = new OmniClient({ apiKey: 'your-api-key-here' });
  
  const predictions = await client.intelligence.predictRevenue();
  console.log(predictions);
</script>
```

## Features

- ✅ **TypeScript Support**: Full type definitions included
- ✅ **Auto-Retry**: Automatic retry with exponential backoff
- ✅ **Error Handling**: Typed exceptions for different error scenarios
- ✅ **Rate Limiting**: Automatic rate limit handling
- ✅ **Browser & Node.js**: Works in both environments
- ✅ **ESM & CommonJS**: Supports both module systems

## Services

### Intelligence Service

```typescript
// Revenue predictions
const predictions = await client.intelligence.predictRevenue({ userId: '123' });

// Business insights
const insights = await client.intelligence.getBusinessInsights('30d');

// Anomaly detection
const anomalies = await client.intelligence.detectAnomalies(dataPoints);

// Churn prediction
const churn = await client.intelligence.predictChurn('123', {
  activityScore: 0.7,
  lastLoginDays: 10
});
```

### AI Service

```typescript
// Text analysis
const analysis = await client.ai.analyzeText(
  'Your text here',
  'sentiment'  // or 'entities', 'summary'
);

// Get available models
const models = await client.ai.getModels();

// Get model details
const modelInfo = await client.ai.getModelDetails('gpt-4-turbo');
```

### Analytics Service

```typescript
// Get dashboard data
const dashboard = await client.analytics.getDashboard();

// Get specific metrics
const metrics = await client.analytics.getMetrics([
  'active_users',
  'revenue',
  'conversion_rate'
]);

// Get dashboard types
const types = await client.analytics.getDashboardTypes();
```

## Error Handling

```typescript
import {
  OmniClient,
  OmniAuthError,
  OmniRateLimitError,
  OmniAPIError
} from '@omni/client';

try {
  const client = new OmniClient({ apiKey: 'your-key' });
  const result = await client.intelligence.predictRevenue();
} catch (error) {
  if (error instanceof OmniAuthError) {
    console.error('Invalid API key');
  } else if (error instanceof OmniRateLimitError) {
    console.error(`Rate limit exceeded. Retry after ${error.retryAfter}s`);
  } else if (error instanceof OmniAPIError) {
    console.error(`API error: ${error.message}`);
  }
}
```

## Configuration

```typescript
const client = new OmniClient({
  apiKey: 'your-key',
  baseURL: 'https://api.omni-platform.com',  // Custom API endpoint
  timeout: 30000,  // Request timeout in milliseconds
  maxRetries: 3,  // Maximum retry attempts
  retryDelay: 1000  // Initial retry delay in milliseconds
});
```

## Requirements

- Node.js 14+ or modern browser
- axios >= 1.6.0

## License

MIT License

## Support

- Documentation: https://docs.omni-platform.com
- Email: support@omni-platform.com
- GitHub Issues: https://github.com/omni-platform/omni-js-sdk/issues
