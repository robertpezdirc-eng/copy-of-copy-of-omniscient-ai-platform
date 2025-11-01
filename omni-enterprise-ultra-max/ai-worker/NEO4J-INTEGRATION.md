# Neo4j Integration Guide

## Overview
Neo4j graph database integration provides advanced recommendation capabilities using graph algorithms and relationship analysis.

## Benefits
- **Collaborative Filtering:** Find products based on similar user behavior patterns
- **Graph Traversal:** Discover hidden connections between users and products
- **Real-time Recommendations:** Fast graph queries for instant personalization
- **Community Detection:** Identify user clusters and trends
- **Pattern Matching:** Advanced Cypher queries for complex recommendations

---

## Setup

### 1. Deploy Neo4j Instance

#### Option A: Neo4j Aura (Cloud - Recommended)
1. Go to https://neo4j.com/cloud/aura/
2. Create free account
3. Create new database (Professional or Enterprise)
4. Note down:
   - Connection URI (bolt://xxx.databases.neo4j.io)
   - Username (usually `neo4j`)
   - Password

#### Option B: Self-Hosted Docker
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-secure-password \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  neo4j:5.14-enterprise
```

#### Option C: GCP Marketplace
Deploy Neo4j from GCP Marketplace with managed infrastructure.

---

### 2. Configure ai-worker Environment

Update Cloud Run service with Neo4j credentials:

```bash
# Set Neo4j environment variables
gcloud run services update omni-ai-worker \
  --region=europe-west1 \
  --project=refined-graph-471712-n9 \
  --set-env-vars="NEO4J_URI=bolt://your-neo4j-uri:7687,NEO4J_USER=neo4j,NEO4J_PASSWORD=your-password"
```

Or add to `ai-worker/.env`:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
```

---

### 3. Initialize Graph Schema

Run these Cypher commands in Neo4j Browser (http://localhost:7474):

```cypher
// Create constraints for unique IDs
CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT product_id IF NOT EXISTS
FOR (p:Product) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT category_name IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;

// Create indexes for performance
CREATE INDEX user_created IF NOT EXISTS
FOR (u:User) ON (u.created_at);

CREATE INDEX product_category IF NOT EXISTS
FOR (p:Product) ON (p.category);

CREATE INDEX interaction_timestamp IF NOT EXISTS
FOR ()-[r:PURCHASED|VIEWED]-() ON (r.last_interaction);
```

---

### 4. Load Sample Data

```cypher
// Create sample users
CREATE (u1:User {id: 'user_001', email: 'alice@example.com', created_at: timestamp()})
CREATE (u2:User {id: 'user_002', email: 'bob@example.com', created_at: timestamp()})
CREATE (u3:User {id: 'user_003', email: 'charlie@example.com', created_at: timestamp()})

// Create sample products
CREATE (p1:Product {id: 'prod_001', name: 'API Marketplace Pro', category: 'marketplace', price: 299.00})
CREATE (p2:Product {id: 'prod_002', name: 'AI Credits 1000', category: 'credits', price: 49.00})
CREATE (p3:Product {id: 'prod_003', name: 'Enterprise Support', category: 'support', price: 499.00})
CREATE (p4:Product {id: 'prod_004', name: 'Analytics Dashboard', category: 'analytics', price: 199.00})

// Create relationships
CREATE (u1)-[:PURCHASED {first_interaction: timestamp(), count: 1}]->(p1)
CREATE (u1)-[:VIEWED {first_interaction: timestamp(), count: 3}]->(p2)
CREATE (u2)-[:PURCHASED {first_interaction: timestamp(), count: 1}]->(p1)
CREATE (u2)-[:PURCHASED {first_interaction: timestamp(), count: 1}]->(p3)
CREATE (u3)-[:VIEWED {first_interaction: timestamp(), count: 2}]->(p1)
CREATE (u3)-[:PURCHASED {first_interaction: timestamp(), count: 1}]->(p4)
```

---

## Usage

### API Endpoints

#### 1. Get Graph-Based Recommendations
```bash
POST /recommend/products
{
  "tenant_id": "default",
  "user_id": "user_001",
  "context": {},
  "top_k": 5
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "product_id": "prod_003",
      "product_name": "Enterprise Support",
      "category": "support",
      "score": 5,
      "reason": "Users similar to you also purchased this",
      "similar_users": ["user_002", "user_005"]
    }
  ]
}
```

#### 2. Track User Interactions
```python
from services.ai.neo4j_graph import get_neo4j_service

neo4j = get_neo4j_service()

# Track a purchase
await neo4j.track_user_interaction(
    user_id="user_001",
    product_id="prod_002",
    interaction_type="PURCHASED"
)

# Track a view
await neo4j.track_user_interaction(
    user_id="user_001",
    product_id="prod_003",
    interaction_type="VIEWED"
)
```

#### 3. Get Trending Products
```python
# Get trending products in last 24 hours
trending = await neo4j.get_trending_products(
    category="marketplace",
    time_window_hours=24,
    limit=10
)
```

#### 4. Find Similar Products
```python
# Find products similar to a given product
similar = await neo4j.get_product_similarities(
    product_id="prod_001",
    limit=5
)
```

---

## Advanced Queries

### Custom Cypher Queries

#### Find Power Users
```cypher
MATCH (u:User)-[r:PURCHASED]->(p:Product)
WITH u, COUNT(p) as purchase_count, SUM(p.price) as total_spent
WHERE purchase_count >= 5
RETURN u.id, u.email, purchase_count, total_spent
ORDER BY total_spent DESC
LIMIT 20
```

#### Product Recommendation via Graph Algorithms
```cypher
// Collaborative filtering with weighted relationships
MATCH (u:User {id: 'user_001'})-[r1:PURCHASED]->(p:Product)<-[r2:PURCHASED]-(similar:User)
MATCH (similar)-[r3:PURCHASED]->(rec:Product)
WHERE NOT (u)-[:PURCHASED]->(rec)
WITH rec, COUNT(DISTINCT similar) as similarity_score,
     SUM(r3.count) as interaction_strength
RETURN rec.id, rec.name, rec.category,
       (similarity_score * 10 + interaction_strength) as total_score
ORDER BY total_score DESC
LIMIT 10
```

#### Find User Communities (Louvain Algorithm)
```cypher
// Requires Graph Data Science library
CALL gds.louvain.stream('user-product-graph')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) as user, communityId
WHERE user:User
RETURN communityId, COUNT(user) as community_size,
       COLLECT(user.email)[0..5] as sample_users
ORDER BY community_size DESC
```

---

## Integration with Backend

### Sync User Actions to Neo4j

Add to `backend/routes/marketplace_routes.py`:

```python
from utils.neo4j_sync import sync_purchase_to_graph

@router.post("/marketplace/purchase")
async def purchase_item(item_id: str, user_id: str):
    # Process purchase
    transaction = await process_purchase(item_id, user_id)
    
    # Sync to Neo4j graph
    await sync_purchase_to_graph(
        user_id=user_id,
        product_id=item_id
    )
    
    return {"status": "success", "transaction_id": transaction.id}
```

Create `backend/utils/neo4j_sync.py`:

```python
import httpx
import os

AI_WORKER_URL = os.getenv("AI_WORKER_URL")

async def sync_purchase_to_graph(user_id: str, product_id: str):
    """Sync purchase event to Neo4j via ai-worker"""
    if not AI_WORKER_URL:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{AI_WORKER_URL}/graph/track",
                json={
                    "user_id": user_id,
                    "product_id": product_id,
                    "interaction_type": "PURCHASED"
                },
                timeout=5.0
            )
    except Exception as e:
        logger.warning(f"Failed to sync to Neo4j: {e}")
```

---

## Monitoring & Maintenance

### Performance Optimization

1. **Add Indexes:**
```cypher
// Index on frequently queried properties
CREATE INDEX product_price IF NOT EXISTS
FOR (p:Product) ON (p.price);

CREATE INDEX user_email IF NOT EXISTS
FOR (u:User) ON (u.email);
```

2. **Monitor Query Performance:**
```cypher
// Check slow queries
CALL dbms.listQueries()
YIELD queryId, query, elapsedTimeMillis
WHERE elapsedTimeMillis > 1000
RETURN queryId, query, elapsedTimeMillis
ORDER BY elapsedTimeMillis DESC;
```

3. **Periodic Maintenance:**
```cypher
// Remove old interactions (older than 1 year)
MATCH ()-[r:VIEWED]->()
WHERE r.last_interaction < timestamp() - (365 * 24 * 3600 * 1000)
DELETE r;
```

### Backup & Recovery

```bash
# Backup Neo4j database
neo4j-admin dump --database=neo4j --to=/backup/neo4j-backup.dump

# Restore from backup
neo4j-admin load --from=/backup/neo4j-backup.dump --database=neo4j --force
```

---

## Cost Optimization

### Neo4j Aura Pricing
- **Free Tier:** 200k nodes, 400k relationships
- **Professional:** $65/month - 1M nodes
- **Enterprise:** Custom pricing

### Self-Hosted Costs (GCP)
- **VM:** e2-standard-4 (~$120/month)
- **Storage:** 100GB SSD (~$17/month)
- **Total:** ~$140/month

### Optimization Tips
1. Use TTL to expire old data
2. Archive historical data to BigQuery
3. Use read replicas for analytics queries
4. Implement caching layer (Redis) for frequent queries

---

## Troubleshooting

### Connection Issues
```python
# Test Neo4j connection
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
with driver.session() as session:
    result = session.run("RETURN 1 as test")
    print(result.single()["test"])  # Should print: 1
driver.close()
```

### Common Errors

**Error:** `ServiceUnavailable: Unable to connect`
- Check Neo4j is running: `docker ps | grep neo4j`
- Verify firewall rules allow port 7687
- Check credentials in environment variables

**Error:** `ConstraintValidationFailed`
- Ensure unique constraints are created
- Check for duplicate IDs in data

**Error:** `OutOfMemoryError`
- Increase heap size in `neo4j.conf`:
  ```
  dbms.memory.heap.initial_size=2G
  dbms.memory.heap.max_size=4G
  ```

---

## Migration from Existing System

### Import from PostgreSQL

```python
# Export from Postgres
import asyncpg
from neo4j import GraphDatabase

pg_conn = await asyncpg.connect("postgresql://...")
neo4j_driver = GraphDatabase.driver("bolt://...", auth=("neo4j", "password"))

# Fetch users and purchases
users = await pg_conn.fetch("SELECT id, email FROM users")
purchases = await pg_conn.fetch("SELECT user_id, product_id FROM transactions WHERE status='completed'")

# Import to Neo4j
with neo4j_driver.session() as session:
    # Create users
    for user in users:
        session.run(
            "MERGE (u:User {id: $id, email: $email})",
            id=user['id'], email=user['email']
        )
    
    # Create purchases
    for purchase in purchases:
        session.run("""
            MATCH (u:User {id: $user_id})
            MATCH (p:Product {id: $product_id})
            MERGE (u)-[:PURCHASED {timestamp: timestamp()}]->(p)
        """, user_id=purchase['user_id'], product_id=purchase['product_id'])

neo4j_driver.close()
```

---

## Resources

- **Neo4j Documentation:** https://neo4j.com/docs/
- **Cypher Query Language:** https://neo4j.com/docs/cypher-manual/current/
- **Graph Data Science Library:** https://neo4j.com/docs/graph-data-science/current/
- **Python Driver:** https://neo4j.com/docs/api/python-driver/current/

---

**Version:** 1.0.0  
**Last Updated:** November 1, 2025  
**Compatible with:** Neo4j 5.x
