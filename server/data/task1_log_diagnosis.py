"""Synthetic log scenarios for Task 1: Log Anomaly Diagnosis."""


def _ts(minute, second=0):
    return f"2026-04-04T14:{minute:02d}:{second:02d}Z"


SCENARIOS = [
    # ── Scenario 1: Database Connection Pool Exhaustion ──
    {
        "id": "db_pool_exhaustion",
        "description": "Production services are experiencing intermittent failures. Investigate the logs to diagnose the incident.",
        "services": {
            "api-gateway": [
                {"timestamp": _ts(0, 1), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/users"},
                {"timestamp": _ts(0, 5), "level": "INFO", "service": "api-gateway", "message": "Request received: POST /api/login"},
                {"timestamp": _ts(1, 10), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/products"},
                {"timestamp": _ts(2, 0), "level": "WARN", "service": "api-gateway", "message": "Upstream user-service responded with 503 Service Unavailable"},
                {"timestamp": _ts(2, 15), "level": "WARN", "service": "api-gateway", "message": "Upstream auth-service latency spike: 4500ms (threshold: 1000ms)"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "service": "api-gateway", "message": "Multiple upstream services degraded, circuit breaker triggered for user-service"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "api-gateway", "message": "5xx error rate at 45%, triggering alert"},
                {"timestamp": _ts(3, 20), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/products (routed to product-service - OK)"},
                {"timestamp": _ts(3, 45), "level": "ERROR", "service": "api-gateway", "message": "Upstream auth-service responded with 500 Internal Server Error"},
                {"timestamp": _ts(4, 0), "level": "INFO", "service": "api-gateway", "message": "Health check: payment-service OK"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "Service started on port 8080"},
                {"timestamp": _ts(0, 10), "level": "INFO", "service": "user-service", "message": "Processing request: GET /users/123"},
                {"timestamp": _ts(1, 0), "level": "WARN", "service": "user-service", "message": "Database query slow: SELECT * FROM users WHERE id=456 took 3200ms"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "service": "user-service", "message": "Failed to acquire database connection from pool: pool exhausted (active=50, max=50)"},
                {"timestamp": _ts(1, 45), "level": "ERROR", "service": "user-service", "message": "ConnectionPoolExhaustedError: Cannot acquire connection, all 50 connections in use, 23 requests waiting"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "user-service", "message": "Database connection timeout after 5000ms: postgres://user-db:5432/users - connection pool max_connections=50 reached"},
                {"timestamp": _ts(2, 10), "level": "ERROR", "service": "user-service", "message": "Request failed: GET /users/789 - could not connect to postgres, pool exhausted"},
                {"timestamp": _ts(2, 30), "level": "WARN", "service": "user-service", "message": "Connection pool stats: active=50/50, idle=0, waiting=35, avg_wait_time=4200ms"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "user-service", "message": "Returning 503 Service Unavailable - database connection pool exhausted"},
                {"timestamp": _ts(3, 30), "level": "ERROR", "service": "user-service", "message": "Health check FAILED: cannot execute SELECT 1 - no available connections in pool"},
            ],
            "auth-service": [
                {"timestamp": _ts(0, 5), "level": "INFO", "service": "auth-service", "message": "Token validation request received"},
                {"timestamp": _ts(0, 30), "level": "INFO", "service": "auth-service", "message": "Session lookup for user_id=123 completed in 15ms"},
                {"timestamp": _ts(1, 15), "level": "WARN", "service": "auth-service", "message": "Slow query: SELECT session FROM sessions WHERE user_id=456 took 2800ms"},
                {"timestamp": _ts(1, 50), "level": "ERROR", "service": "auth-service", "message": "Failed to validate token: database connection timeout (postgres pool exhausted)"},
                {"timestamp": _ts(2, 5), "level": "ERROR", "service": "auth-service", "message": "Cannot acquire DB connection for session lookup: pool=50/50, timeout=5000ms"},
                {"timestamp": _ts(2, 25), "level": "ERROR", "service": "auth-service", "message": "Authentication failed for request: unable to reach user-db, connection pool limit reached"},
                {"timestamp": _ts(2, 50), "level": "WARN", "service": "auth-service", "message": "Falling back to cached session data for user_id=789 (stale: 15min)"},
                {"timestamp": _ts(3, 10), "level": "ERROR", "service": "auth-service", "message": "Returning 500: persistent database connection pool exhaustion on postgres://user-db:5432"},
            ],
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "Payment processed: order_id=1001 amount=$49.99 status=success"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "payment-service", "message": "Payment processed: order_id=1002 amount=$125.00 status=success"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "payment-service", "message": "Payment gateway health check: OK"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "payment-service", "message": "Payment processed: order_id=1003 amount=$75.50 status=success"},
                {"timestamp": _ts(4, 0), "level": "INFO", "service": "payment-service", "message": "Daily reconciliation batch started"},
            ],
            "product-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "product-service", "message": "Cache hit for product_id=501"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "product-service", "message": "Product search query completed in 45ms"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "product-service", "message": "Inventory sync completed successfully"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "product-service", "message": "Cache refresh: 1200 products updated"},
            ],
        },
        "ground_truth": {
            "incident_type": "database_connection_pool_exhaustion",
            "severity": "P2",
            "affected_services": ["user-service", "auth-service", "api-gateway"],
            "root_cause_keywords": ["connection pool", "exhausted", "max_connections", "postgres", "database"],
        },
        "relevant_services": ["user-service", "auth-service"],
        "relevant_search_terms": ["pool", "exhausted", "connection", "max_connections", "timeout", "503"],
    },

    # ── Scenario 2: Memory Leak ──
    {
        "id": "memory_leak",
        "description": "A service is experiencing performance degradation over time. Investigate the logs to identify the issue.",
        "services": {
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/reports"},
                {"timestamp": _ts(5, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/dashboard"},
                {"timestamp": _ts(10, 0), "level": "WARN", "service": "api-gateway", "message": "Upstream worker-service response time: 8500ms (threshold: 2000ms)"},
                {"timestamp": _ts(12, 0), "level": "ERROR", "service": "api-gateway", "message": "Upstream worker-service returned 500 Internal Server Error"},
                {"timestamp": _ts(14, 0), "level": "ERROR", "service": "api-gateway", "message": "worker-service circuit breaker OPEN after 5 consecutive failures"},
            ],
            "worker-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "worker-service", "message": "Service started, heap size: 512MB, used: 120MB"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "worker-service", "message": "Processing report generation batch, heap used: 280MB"},
                {"timestamp": _ts(4, 0), "level": "WARN", "service": "worker-service", "message": "GC pause: 450ms, heap used: 420MB/512MB (82%), objects not collected: 15000"},
                {"timestamp": _ts(6, 0), "level": "WARN", "service": "worker-service", "message": "Memory usage critical: heap 485MB/512MB (95%), old_gen occupancy growing linearly"},
                {"timestamp": _ts(7, 0), "level": "ERROR", "service": "worker-service", "message": "GC overhead limit exceeded: spending 98% of time in garbage collection, heap 505MB/512MB"},
                {"timestamp": _ts(8, 0), "level": "ERROR", "service": "worker-service", "message": "OutOfMemoryError: Java heap space - failed to allocate 16MB for report buffer. Suspected leak in ReportCache: 12000 cached entries never evicted"},
                {"timestamp": _ts(9, 0), "level": "ERROR", "service": "worker-service", "message": "Service unresponsive, heap dump triggered: /tmp/heapdump-2026-04-04.hprof"},
                {"timestamp": _ts(10, 0), "level": "ERROR", "service": "worker-service", "message": "Memory leak detected: ReportCache holding 450MB of unreferenced report objects, cache eviction policy disabled since deploy v2.3.1"},
                {"timestamp": _ts(11, 0), "level": "ERROR", "service": "worker-service", "message": "Process killed by OOM killer, exit code 137"},
            ],
            "notification-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "notification-service", "message": "Email sent: user_id=101 template=welcome"},
                {"timestamp": _ts(5, 0), "level": "INFO", "service": "notification-service", "message": "Push notification delivered: user_id=202"},
                {"timestamp": _ts(10, 0), "level": "INFO", "service": "notification-service", "message": "SMS sent: user_id=303 status=delivered"},
                {"timestamp": _ts(12, 0), "level": "WARN", "service": "notification-service", "message": "Failed to fetch report status from worker-service: connection refused"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "User login: user_id=123"},
                {"timestamp": _ts(5, 0), "level": "INFO", "service": "user-service", "message": "Profile update: user_id=456"},
                {"timestamp": _ts(10, 0), "level": "INFO", "service": "user-service", "message": "User session refresh: user_id=789"},
            ],
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "Payment processed: order_id=2001 status=success"},
                {"timestamp": _ts(5, 0), "level": "INFO", "service": "payment-service", "message": "Refund issued: order_id=1999 status=success"},
            ],
        },
        "ground_truth": {
            "incident_type": "memory_leak",
            "severity": "P2",
            "affected_services": ["worker-service", "api-gateway"],
            "root_cause_keywords": ["memory", "leak", "heap", "OutOfMemoryError", "ReportCache", "eviction"],
        },
        "relevant_services": ["worker-service"],
        "relevant_search_terms": ["memory", "heap", "OOM", "OutOfMemory", "leak", "GC", "cache"],
    },

    # ── Scenario 3: TLS Certificate Expiration ──
    {
        "id": "cert_expiry",
        "description": "Users are reporting they cannot access the application. Multiple error reports are coming in. Investigate.",
        "services": {
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Incoming request: GET /api/dashboard"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "service": "api-gateway", "message": "TLS handshake failed with auth-service: certificate has expired (expired: 2026-04-03T23:59:59Z)"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "api-gateway", "message": "SSL_ERROR_EXPIRED_CERT_ALERT: peer certificate expired for auth-service.internal:443"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "service": "api-gateway", "message": "Cannot establish secure connection to auth-service: x509 certificate has expired or is not yet valid"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "api-gateway", "message": "All authentication requests failing: TLS certificate expired on auth-service"},
                {"timestamp": _ts(2, 30), "level": "WARN", "service": "api-gateway", "message": "Bypassing auth for health check endpoints only"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "api-gateway", "message": "Returning 502 Bad Gateway for all authenticated routes"},
            ],
            "auth-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "auth-service", "message": "Service running on port 443 with TLS enabled"},
                {"timestamp": _ts(0, 15), "level": "WARN", "service": "auth-service", "message": "TLS certificate expires in 0 days! CN=auth-service.internal, issuer=internal-ca, notAfter=2026-04-03T23:59:59Z"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "service": "auth-service", "message": "TLS certificate EXPIRED: /etc/ssl/certs/auth-service.pem expired at 2026-04-03T23:59:59Z"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "auth-service", "message": "Incoming TLS connections being rejected: certificate expired, clients receiving SSL_ERROR_EXPIRED_CERT_ALERT"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "service": "auth-service", "message": "Auto-renewal failed: certbot renewal returned exit code 1 - ACME challenge failed, DNS record not found"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "auth-service", "message": "Manual certificate renewal required: /etc/ssl/certs/auth-service.pem"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "Processing request: GET /users/list"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "user-service", "message": "Failed to call auth-service for token validation: SSL certificate problem: certificate has expired"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "user-service", "message": "All auth-dependent requests failing due to expired TLS cert on auth-service"},
            ],
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "Payment processed: order_id=3001 status=success"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "payment-service", "message": "Payment gateway connection OK (separate TLS cert)"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "payment-service", "message": "Daily batch processing completed"},
            ],
            "product-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "product-service", "message": "Product catalog sync completed"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "product-service", "message": "Search index updated: 1500 products"},
            ],
        },
        "ground_truth": {
            "incident_type": "tls_certificate_expiration",
            "severity": "P1",
            "affected_services": ["auth-service", "api-gateway", "user-service"],
            "root_cause_keywords": ["certificate", "expired", "TLS", "SSL", "renewal", "auth-service"],
        },
        "relevant_services": ["auth-service", "api-gateway"],
        "relevant_search_terms": ["certificate", "expired", "TLS", "SSL", "x509", "cert"],
    },

    # ── Scenario 4: Rate Limiting / Throttling ──
    {
        "id": "rate_limiting",
        "description": "Some API consumers are reporting 429 errors. Investigate what is happening.",
        "services": {
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/search from client_id=bot-scraper-x"},
                {"timestamp": _ts(0, 1), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/search from client_id=bot-scraper-x"},
                {"timestamp": _ts(0, 2), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/search from client_id=bot-scraper-x"},
                {"timestamp": _ts(0, 5), "level": "WARN", "service": "api-gateway", "message": "Rate limit exceeded for client_id=bot-scraper-x: 500 requests/min (limit: 100/min)"},
                {"timestamp": _ts(0, 10), "level": "WARN", "service": "api-gateway", "message": "Rate limiter: client_id=bot-scraper-x throttled, returning 429 Too Many Requests"},
                {"timestamp": _ts(0, 30), "level": "WARN", "service": "api-gateway", "message": "Rate limit bucket overflow: client_id=bot-scraper-x at 1200 req/min, blocking all requests"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "api-gateway", "message": "Aggressive client bot-scraper-x consuming 60% of total request capacity, impacting other clients"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "service": "api-gateway", "message": "Global rate limit approaching: 8500/10000 req/min, primarily from bot-scraper-x"},
                {"timestamp": _ts(2, 0), "level": "WARN", "service": "api-gateway", "message": "Legitimate client client_id=mobile-app receiving 429s due to shared rate limit bucket exhaustion"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "service": "api-gateway", "message": "Global rate limit EXCEEDED: 10500/10000 req/min, all clients now throttled"},
            ],
            "product-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "product-service", "message": "Search query from api-gateway: q=electronics"},
                {"timestamp": _ts(0, 5), "level": "WARN", "service": "product-service", "message": "High request volume: 400 search queries in last 60s (normal: 50)"},
                {"timestamp": _ts(0, 30), "level": "WARN", "service": "product-service", "message": "Search index under heavy load, p99 latency: 2500ms (normal: 200ms)"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "product-service", "message": "Elasticsearch connection pool saturated: 50/50 connections in use due to excessive search queries"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "service": "product-service", "message": "Search requests queuing, avg response time: 5000ms"},
            ],
            "auth-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "auth-service", "message": "API key validated: client_id=bot-scraper-x"},
                {"timestamp": _ts(0, 10), "level": "INFO", "service": "auth-service", "message": "API key validated: client_id=mobile-app"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "auth-service", "message": "Token refresh: client_id=web-frontend"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "User lookup completed in 12ms"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "user-service", "message": "Profile fetch for user_id=100 completed"},
            ],
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "No pending transactions"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "payment-service", "message": "Payment gateway health: OK"},
            ],
        },
        "ground_truth": {
            "incident_type": "rate_limiting",
            "severity": "P3",
            "affected_services": ["api-gateway", "product-service"],
            "root_cause_keywords": ["rate limit", "throttl", "429", "bot-scraper", "requests per minute", "capacity"],
        },
        "relevant_services": ["api-gateway", "product-service"],
        "relevant_search_terms": ["rate limit", "429", "throttl", "bot-scraper", "capacity", "Too Many Requests"],
    },

    # ── Scenario 5: Disk Space Exhaustion ──
    {
        "id": "disk_full",
        "description": "The logging and monitoring systems are reporting anomalies. Some data may be missing. Investigate.",
        "services": {
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: POST /api/upload"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/reports/download"},
                {"timestamp": _ts(5, 0), "level": "WARN", "service": "api-gateway", "message": "Upstream logging-service returned 500"},
                {"timestamp": _ts(7, 0), "level": "ERROR", "service": "api-gateway", "message": "Audit log write failed: logging-service unavailable"},
            ],
            "logging-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "logging-service", "message": "Log ingestion: 5000 events/sec, disk usage: 85%"},
                {"timestamp": _ts(1, 0), "level": "WARN", "service": "logging-service", "message": "Disk usage WARNING: /var/log at 92% (460GB/500GB)"},
                {"timestamp": _ts(2, 0), "level": "WARN", "service": "logging-service", "message": "Disk usage CRITICAL: /var/log at 97% (485GB/500GB), log rotation failed: no space for rotated files"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "logging-service", "message": "ENOSPC: No space left on device - cannot write to /var/log/app.log"},
                {"timestamp": _ts(3, 30), "level": "ERROR", "service": "logging-service", "message": "Disk full: /var/log at 100% (500GB/500GB). All log writes failing. Old logs not cleaned: retention policy set to 365 days"},
                {"timestamp": _ts(4, 0), "level": "ERROR", "service": "logging-service", "message": "Elasticsearch indexing halted: no disk space for new indices on /var/data"},
                {"timestamp": _ts(5, 0), "level": "ERROR", "service": "logging-service", "message": "Service degraded: dropping incoming log events, data loss occurring"},
                {"timestamp": _ts(6, 0), "level": "ERROR", "service": "logging-service", "message": "Health check FAILED: disk /var/log 100%, /var/data 99%"},
            ],
            "monitoring-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "monitoring-service", "message": "Metrics collection cycle completed"},
                {"timestamp": _ts(2, 0), "level": "WARN", "service": "monitoring-service", "message": "Cannot write metrics to logging-service: connection refused"},
                {"timestamp": _ts(4, 0), "level": "ERROR", "service": "monitoring-service", "message": "Metrics data loss: 3000 data points dropped, logging-service not accepting writes"},
                {"timestamp": _ts(5, 0), "level": "WARN", "service": "monitoring-service", "message": "Falling back to local buffer, local disk at 70%"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "Request processed: GET /users/list in 25ms"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "user-service", "message": "Request processed: POST /users/create in 45ms"},
                {"timestamp": _ts(5, 0), "level": "WARN", "service": "user-service", "message": "Audit logging failed: logging-service returned 500"},
            ],
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "Transaction completed: order_id=4001"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "payment-service", "message": "Transaction completed: order_id=4002"},
            ],
        },
        "ground_truth": {
            "incident_type": "disk_space_exhaustion",
            "severity": "P2",
            "affected_services": ["logging-service", "monitoring-service", "api-gateway"],
            "root_cause_keywords": ["disk", "space", "full", "ENOSPC", "storage", "retention", "no space left"],
        },
        "relevant_services": ["logging-service", "monitoring-service"],
        "relevant_search_terms": ["disk", "space", "ENOSPC", "full", "storage", "retention", "no space"],
    },

    # ── Scenario 6: DNS Resolution Failure ──
    {
        "id": "dns_resolution_failure",
        "description": "Multiple services are intermittently failing to connect to each other. Some requests succeed while others fail with no clear pattern. Investigate.",
        "services": {
            "dns-resolver": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "dns-resolver", "message": "CoreDNS v1.11.1 started, serving internal zone .internal"},
                {"timestamp": _ts(1, 0), "level": "WARN", "service": "dns-resolver", "message": "Query rate 3500 qps approaching capacity (max: 2000 qps)"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "dns-resolver", "message": "Query rate 5000 qps exceeds capacity (max: 2000 qps), dropping queries"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "service": "dns-resolver", "message": "SERVFAIL for user-db.internal: cache entry corrupted after OOM event on resolver pod"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "dns-resolver", "message": "OOM killed: resolver process exceeded 256MB memory limit, restarting"},
                {"timestamp": _ts(3, 30), "level": "ERROR", "service": "dns-resolver", "message": "DNS cache cleared after restart, all entries evicted. Cold cache causing query amplification"},
                {"timestamp": _ts(4, 0), "level": "ERROR", "service": "dns-resolver", "message": "SERVFAIL rate at 35%: unable to resolve auth-service.internal, user-db.internal for 40% of queries"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/users"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: POST /api/login"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "api-gateway", "message": "Failed to resolve hostname auth-service.internal: ENOTFOUND (DNS query returned SERVFAIL)"},
                {"timestamp": _ts(2, 20), "level": "INFO", "service": "api-gateway", "message": "Request to auth-service succeeded (cached DNS entry used)"},
                {"timestamp": _ts(2, 40), "level": "ERROR", "service": "api-gateway", "message": "getaddrinfo ENOTFOUND user-service.internal - DNS resolution failed"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "api-gateway", "message": "Intermittent upstream failures: 40% of requests failing with ENOTFOUND across multiple services"},
                {"timestamp": _ts(3, 30), "level": "ERROR", "service": "api-gateway", "message": "Service discovery via DNS unreliable, cannot consistently resolve *.internal hostnames"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "Service started on port 8080"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "user-service", "message": "Processing request: GET /users/123"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "user-service", "message": "getaddrinfo ENOTFOUND user-db.internal - DNS resolution failed for database host"},
                {"timestamp": _ts(2, 30), "level": "INFO", "service": "user-service", "message": "Retried connection to user-db.internal: succeeded (DNS cached)"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "user-service", "message": "3 of 5 database connection attempts failed: ENOTFOUND user-db.internal - name resolution intermittent"},
                {"timestamp": _ts(3, 30), "level": "ERROR", "service": "user-service", "message": "Health check unstable: DNS for user-db.internal resolves on some attempts, SERVFAIL on others"},
            ],
            "product-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "product-service", "message": "Connected to product-db at 10.0.1.50:5432 (IP-based, no DNS)"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "product-service", "message": "Product query completed in 30ms"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "product-service", "message": "Cache refresh completed, 800 products indexed"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "product-service", "message": "All systems nominal, product-db connection stable via static IP"},
            ],
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "Payment processed: order_id=5001 status=success"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "payment-service", "message": "Payment gateway connection OK (static config: 10.0.2.100:443)"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "payment-service", "message": "Transaction completed: order_id=5002 status=success"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "payment-service", "message": "Daily batch reconciliation completed"},
            ],
        },
        "ground_truth": {
            "incident_type": "dns_resolution_failure",
            "severity": "P1",
            "affected_services": ["dns-resolver", "api-gateway", "user-service"],
            "root_cause_keywords": ["DNS", "resolution", "SERVFAIL", "ENOTFOUND", "resolver", "name resolution"],
        },
        "relevant_services": ["dns-resolver", "api-gateway", "user-service"],
        "relevant_search_terms": ["DNS", "ENOTFOUND", "SERVFAIL", "resolve", "name resolution", "getaddrinfo"],
    },

    # ── Scenario 7: Kafka Consumer Lag ──
    {
        "id": "kafka_consumer_lag",
        "description": "Background job processing has stopped and users are complaining that their notifications and emails are significantly delayed. Investigate.",
        "services": {
            "queue": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "queue", "message": "Kafka broker started, topic 'events' has 4 partitions"},
                {"timestamp": _ts(1, 0), "level": "WARN", "service": "queue", "message": "Consumer group 'worker-group' rebalancing: member worker-3 timed out (session.timeout.ms=10000, last heartbeat 15s ago)"},
                {"timestamp": _ts(1, 30), "level": "WARN", "service": "queue", "message": "Consumer group 'worker-group' rebalancing again: 3rd rebalance in 60 seconds"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "queue", "message": "Partition lag for topic 'events': partition-0 lag=45000, partition-1 lag=38000, partition-2 lag=42000, partition-3 lag=35000"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "queue", "message": "Total consumer lag: 160000 messages across 4 partitions, no consumer making progress"},
                {"timestamp": _ts(4, 0), "level": "ERROR", "service": "queue", "message": "Consumer group 'worker-group' in perpetual rebalance: 12 rebalances in 4 minutes, 0 committed offsets"},
            ],
            "worker": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "worker", "message": "Worker started, joining consumer group 'worker-group' on topic 'events'"},
                {"timestamp": _ts(0, 30), "level": "INFO", "service": "worker", "message": "Partitions assigned: [events-0, events-1], consuming messages"},
                {"timestamp": _ts(1, 0), "level": "WARN", "service": "worker", "message": "ConsumerRebalanceListener: partitions revoked, rejoining group"},
                {"timestamp": _ts(1, 30), "level": "WARN", "service": "worker", "message": "Rebalance triggered again before processing could start: session.timeout.ms=10000 too low for 5s poll interval"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "worker", "message": "Consumer stuck in REBALANCING state, no messages processed for 120s"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "service": "worker", "message": "5th rebalance in 2 minutes: max.poll.interval.ms=300000 but session.timeout.ms=10000 causing premature member eviction"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "worker", "message": "0 messages consumed since startup, all time spent in rebalance cycles"},
                {"timestamp": _ts(3, 30), "level": "ERROR", "service": "worker", "message": "Worker effectively dead: continuous JoinGroup/LeaveGroup loop, cannot hold partition assignment"},
            ],
            "notification-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "notification-service", "message": "Listening for notification events from worker pipeline"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "notification-service", "message": "Last notification processed 120s ago (normal interval: 1-2s)"},
                {"timestamp": _ts(2, 0), "level": "WARN", "service": "notification-service", "message": "Event pipeline empty: 0 events received in last 300s (expected: ~500)"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "notification-service", "message": "No incoming events for 5 minutes, 2400 pending notifications queued locally, none delivered"},
                {"timestamp": _ts(4, 0), "level": "ERROR", "service": "notification-service", "message": "User complaints increasing: 150 support tickets about missing/delayed email notifications"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: GET /api/users"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: POST /api/orders"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "api-gateway", "message": "All synchronous routes responding normally"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "api-gateway", "message": "Health check: all upstream services OK (note: async notification pipeline not monitored)"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "User profile update completed in 20ms"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "user-service", "message": "User registration: user_id=567"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "user-service", "message": "Session refresh completed for user_id=890"},
            ],
        },
        "ground_truth": {
            "incident_type": "message_queue_consumer_lag",
            "severity": "P2",
            "affected_services": ["queue", "worker", "notification-service"],
            "root_cause_keywords": ["consumer", "lag", "rebalance", "Kafka", "session timeout", "partition"],
        },
        "relevant_services": ["queue", "worker", "notification-service"],
        "relevant_search_terms": ["consumer", "lag", "rebalance", "partition", "Kafka", "session timeout", "JoinGroup"],
    },

    # ── Scenario 8: Network/Firewall Timeout ──
    {
        "id": "upstream_api_timeout",
        "description": "The checkout flow is failing for all users. Payment processing seems broken but the payment gateway itself claims it is healthy. Investigate.",
        "services": {
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-service", "message": "Processing payment: order_id=6001, amount=$89.99"},
                {"timestamp": _ts(0, 10), "level": "WARN", "service": "payment-service", "message": "POST https://payment-gateway.external:443/v1/charge timeout after 10000ms - ETIMEDOUT"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "service": "payment-service", "message": "TCP connection established to payment-gateway.external:443 but response never received (socket hang up after 10s)"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "payment-service", "message": "3 consecutive payment timeouts: ETIMEDOUT on all requests to payment-gateway.external"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "service": "payment-service", "message": "Traceroute shows 45% packet loss at hop 7 (fw-egress-02.internal) — possible firewall rule change"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "payment-service", "message": "All outbound connections to payment-gateway.external timing out: packets leaving fw-egress-02 are being dropped"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "service": "payment-service", "message": "Payment success rate: 0% in last 3 minutes (was 99.9% before 14:00). Network path to payment-gateway broken at firewall."},
                {"timestamp": _ts(3, 0), "level": "ERROR", "service": "payment-service", "message": "Returning 504 Gateway Timeout for all payment requests"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "api-gateway", "message": "Request received: POST /api/checkout"},
                {"timestamp": _ts(0, 15), "level": "INFO", "service": "api-gateway", "message": "Forwarding payment request to payment-service"},
                {"timestamp": _ts(0, 30), "level": "WARN", "service": "api-gateway", "message": "payment-service response time: 10200ms (threshold: 5000ms)"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "service": "api-gateway", "message": "Upstream payment-service returning 504 Gateway Timeout for all /api/checkout requests"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "service": "api-gateway", "message": "Checkout endpoint failure rate: 100%, returning 502 to clients"},
                {"timestamp": _ts(2, 30), "level": "INFO", "service": "api-gateway", "message": "Non-payment routes (users, products, search) operating normally"},
            ],
            "payment-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "payment-gateway", "message": "Payment gateway v3.1 running, health check OK"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "payment-gateway", "message": "Internal health check: OK, 0 errors in last 5 min"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "payment-gateway", "message": "System status: healthy, processing 0 requests (no inbound traffic received)"},
                {"timestamp": _ts(3, 0), "level": "INFO", "service": "payment-gateway", "message": "Health check: OK (note: checks internal connectivity only, does not verify inbound reachability)"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "user-service", "message": "User lookup completed in 15ms"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "user-service", "message": "Profile update for user_id=234 completed"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "user-service", "message": "Session validation: user_id=567 OK"},
            ],
            "product-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "service": "product-service", "message": "Product search completed in 40ms"},
                {"timestamp": _ts(1, 0), "level": "INFO", "service": "product-service", "message": "Inventory sync OK, 1500 products available"},
                {"timestamp": _ts(2, 0), "level": "INFO", "service": "product-service", "message": "Cache hit rate: 95%, all systems normal"},
            ],
        },
        "ground_truth": {
            "incident_type": "network_timeout",
            "severity": "P1",
            "affected_services": ["payment-service", "api-gateway"],
            "root_cause_keywords": ["timeout", "network", "firewall", "ETIMEDOUT", "socket", "packet loss", "payment-gateway"],
        },
        "relevant_services": ["payment-service", "api-gateway", "payment-gateway"],
        "relevant_search_terms": ["timeout", "ETIMEDOUT", "firewall", "packet loss", "504", "socket", "payment"],
    },
]
