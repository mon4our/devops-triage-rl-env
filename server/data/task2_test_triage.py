"""Synthetic test failure scenarios for Task 2: CI/CD Test Failure Triage."""

SCENARIOS = [
    # ── Scenario 1: E-commerce Checkout Flow ──
    {
        "id": "ecommerce_checkout",
        "app_description": "E-commerce web application — checkout and payment flow E2E tests run on every PR via Playwright.",
        "test_summary": {"total": 24, "passed": 19, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_cart_total_with_discount",
                "name": "Cart total calculation applies percentage discount correctly",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected cart total to be $45.00 but got $50.00\n"
                    "  at test/e2e/cart.spec.js:47\n"
                    "  Expected: '$45.00'\n"
                    "  Received: '$50.00'"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/cart.spec.js:47:35)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)\n"
                    "    at resolve (node_modules/jest/build/jasmine.js:64:11)"
                ),
                "console_logs": [
                    "[INFO] Cart loaded with 2 items: Widget A ($25.00), Widget B ($25.00)",
                    "[INFO] Applying discount code SAVE10 (10% off)",
                    "[WARN] Discount service returned discount_percent=0 for code SAVE10",
                    "[INFO] Cart total calculated: $50.00",
                ],
                "dom_snapshot": '<div class="cart-summary"><span class="subtotal">$50.00</span><span class="discount">-$0.00</span><span class="total" data-testid="cart-total">$50.00</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["discount", "0%", "regression", "SAVE10", "calculation", "recent change"],
            },
            {
                "test_id": "test_payment_redirect",
                "name": "Payment gateway redirects to confirmation page after successful payment",
                "category": "flaky_test",
                "error_output": (
                    "TimeoutError: Waiting for selector '.confirmation-page' exceeded 5000ms timeout\n"
                    "  at test/e2e/payment.spec.js:82"
                ),
                "stack_trace": (
                    "TimeoutError: waiting for selector '.confirmation-page'\n"
                    "    at ElementHandle.waitForSelector (node_modules/playwright/lib/dom.js:145:15)\n"
                    "    at test/e2e/payment.spec.js:82:20"
                ),
                "console_logs": [
                    "[INFO] Payment form submitted with card ending 4242",
                    "[INFO] Payment processing... waiting for gateway response",
                    "[INFO] Gateway response received after 4800ms",
                    "[WARN] Confirmation page render started but selector not yet in DOM",
                ],
                "dom_snapshot": '<div class="payment-processing"><div class="spinner">Processing...</div></div>',
                "history": [True, False, True, True, False, True, False, True, True, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "timeout", "inconsistent", "flaky", "timing", "race condition", "history"],
            },
            {
                "test_id": "test_inventory_check_api",
                "name": "Inventory check returns stock availability before adding to cart",
                "category": "environment_issue",
                "error_output": (
                    "Error: Request to https://inventory-api.staging.internal/v2/stock failed\n"
                    "  FetchError: connect ECONNREFUSED 10.0.3.45:443\n"
                    "  at test/e2e/inventory.spec.js:31"
                ),
                "stack_trace": (
                    "FetchError: request to https://inventory-api.staging.internal/v2/stock failed\n"
                    "    reason: connect ECONNREFUSED 10.0.3.45:443\n"
                    "    at ClientRequest.<anonymous> (node_modules/node-fetch/lib/index.js:1461:11)\n"
                    "    at test/e2e/inventory.spec.js:31:28"
                ),
                "console_logs": [
                    "[INFO] Fetching stock for product_id=SKU-001",
                    "[ERROR] inventory-api.staging.internal:443 - ECONNREFUSED",
                    "[ERROR] Inventory API unreachable - staging environment DNS resolution failed",
                    "[WARN] Staging inventory service was scheduled for maintenance window 14:00-15:00 UTC",
                ],
                "dom_snapshot": '<div class="product-page"><span class="stock-status">Checking availability...</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["ECONNREFUSED", "staging", "maintenance", "external", "infrastructure", "DNS"],
            },
            {
                "test_id": "test_order_confirmation_email",
                "name": "Order confirmation displays correct shipping address format",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected element '.shipping-address' to contain '123 Main St, Apt 4B, New York, NY 10001'\n"
                    "  but got '123 Main St\\nApt 4B\\nNew York, NY 10001'\n"
                    "  at test/e2e/order.spec.js:95"
                ),
                "stack_trace": (
                    "Error: expect(received).toContain(expected)\n"
                    "    at Object.<anonymous> (test/e2e/order.spec.js:95:42)"
                ),
                "console_logs": [
                    "[INFO] Order #5001 created successfully",
                    "[INFO] Shipping address formatted with new multi-line layout (JIRA-2345)",
                    "[INFO] Confirmation page rendered with updated address component v2",
                ],
                "dom_snapshot": '<div class="shipping-address"><p>123 Main St</p><p>Apt 4B</p><p>New York, NY 10001</p></div>',
                "history": [True, True, True, True, True, True, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["format change", "stale", "outdated", "assertion", "new layout", "JIRA-2345", "intentional"],
            },
            {
                "test_id": "test_search_results_pagination",
                "name": "Search results show correct page count and navigate between pages",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected page count to be 5 but got 1\n"
                    "  Element '.pagination' shows '1 of 1' instead of '1 of 5'\n"
                    "  at test/e2e/search.spec.js:63"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/search.spec.js:63:29)"
                ),
                "console_logs": [
                    "[INFO] Search query: 'laptop' returned 47 results",
                    "[WARN] Pagination component received totalPages=1 (expected 5 for 47 results at 10/page)",
                    "[ERROR] calculatePageCount returned Math.floor(47/10)=4 instead of Math.ceil(47/10)=5. Bug in src/utils/pagination.js line 12",
                ],
                "dom_snapshot": '<div class="search-results"><div class="pagination"><span>Page 1 of 1</span><button class="next" disabled>Next</button></div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["pagination", "Math.floor", "Math.ceil", "calculation", "bug", "recent change"],
            },
        ],
        "recent_changes": [
            {
                "commit": "a1b2c3d",
                "author": "sarah.dev",
                "message": "Refactor discount service client to use new API v2 endpoint",
                "files_changed": ["src/services/discount.js", "src/cart/calculateTotal.js"],
                "diff": (
                    "--- a/src/services/discount.js\n"
                    "+++ b/src/services/discount.js\n"
                    "@@ -15,7 +15,7 @@\n"
                    " async function getDiscount(code) {\n"
                    "-  const resp = await fetch(`/api/v1/discounts/${code}`);\n"
                    "-  return resp.json(); // returns {discount_percent: 10}\n"
                    "+  const resp = await fetch(`/api/v2/discounts/${code}`);\n"
                    "+  const data = await resp.json(); // v2 returns {discount: {percentage: 10}}\n"
                    "+  return {discount_percent: data.discount_percent}; // BUG: should be data.discount.percentage\n"
                ),
            },
            {
                "commit": "e4f5g6h",
                "author": "mike.dev",
                "message": "Update search pagination utility to fix off-by-one",
                "files_changed": ["src/utils/pagination.js"],
                "diff": (
                    "--- a/src/utils/pagination.js\n"
                    "+++ b/src/utils/pagination.js\n"
                    "@@ -10,5 +10,5 @@\n"
                    " function calculatePageCount(totalResults, perPage) {\n"
                    "-  return Math.ceil(totalResults / perPage);\n"
                    "+  return Math.floor(totalResults / perPage); // BUG: wrong rounding\n"
                    " }\n"
                ),
            },
            {
                "commit": "i7j8k9l",
                "author": "anna.dev",
                "message": "Redesign shipping address display to multi-line format (JIRA-2345)",
                "files_changed": ["src/components/ShippingAddress.jsx"],
                "diff": (
                    "--- a/src/components/ShippingAddress.jsx\n"
                    "+++ b/src/components/ShippingAddress.jsx\n"
                    "@@ -5,3 +5,7 @@\n"
                    "-  return <span className='shipping-address'>{formatSingleLine(address)}</span>\n"
                    "+  return (\n"
                    "+    <div className='shipping-address'>\n"
                    "+      <p>{address.street}</p>\n"
                    "+      <p>{address.unit}</p>\n"
                    "+      <p>{address.city}, {address.state} {address.zip}</p>\n"
                    "+    </div>\n"
                    "+  )\n"
                ),
            },
        ],
        "source_files": {
            "src/services/discount.js": (
                "const API_BASE = '/api/v2/discounts';\n\n"
                "async function getDiscount(code) {\n"
                "  const resp = await fetch(`${API_BASE}/${code}`);\n"
                "  const data = await resp.json();\n"
                "  // v2 API returns {discount: {percentage: 10, type: 'percent'}}\n"
                "  return {discount_percent: data.discount_percent}; // BUG: should be data.discount.percentage\n"
                "}\n\n"
                "module.exports = { getDiscount };\n"
            ),
            "src/cart/calculateTotal.js": (
                "const { getDiscount } = require('../services/discount');\n\n"
                "async function calculateTotal(items, discountCode) {\n"
                "  const subtotal = items.reduce((sum, item) => sum + item.price, 0);\n"
                "  if (discountCode) {\n"
                "    const disc = await getDiscount(discountCode);\n"
                "    const discountAmount = subtotal * (disc.discount_percent / 100);\n"
                "    return subtotal - discountAmount;\n"
                "  }\n"
                "  return subtotal;\n"
                "}\n\n"
                "module.exports = { calculateTotal };\n"
            ),
            "src/utils/pagination.js": (
                "function calculatePageCount(totalResults, perPage) {\n"
                "  return Math.floor(totalResults / perPage); // should be Math.ceil\n"
                "}\n\n"
                "module.exports = { calculatePageCount };\n"
            ),
            "src/components/ShippingAddress.jsx": (
                "import React from 'react';\n\n"
                "function ShippingAddress({ address }) {\n"
                "  return (\n"
                "    <div className='shipping-address'>\n"
                "      <p>{address.street}</p>\n"
                "      <p>{address.unit}</p>\n"
                "      <p>{address.city}, {address.state} {address.zip}</p>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default ShippingAddress;\n"
            ),
            "test/e2e/cart.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('cart total with discount', async ({ page }) => {\n"
                "  await page.goto('/cart');\n"
                "  await page.fill('#discount-code', 'SAVE10');\n"
                "  await page.click('#apply-discount');\n"
                "  await page.waitForTimeout(1000);\n"
                "  const total = await page.textContent('[data-testid=\"cart-total\"]');\n"
                "  expect(total).toBe('$45.00'); // line 47\n"
                "});\n"
            ),
            "test/e2e/payment.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('payment redirect to confirmation', async ({ page }) => {\n"
                "  await page.goto('/checkout/payment');\n"
                "  await page.fill('#card-number', '4242424242424242');\n"
                "  await page.fill('#expiry', '12/27');\n"
                "  await page.fill('#cvv', '123');\n"
                "  await page.click('#submit-payment');\n"
                "  // This timeout is too tight for slow gateway responses\n"
                "  await page.waitForSelector('.confirmation-page', { timeout: 5000 }); // line 82\n"
                "  const msg = await page.textContent('.confirmation-message');\n"
                "  expect(msg).toContain('Thank you');\n"
                "});\n"
            ),
            "test/e2e/order.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('order confirmation shows shipping address', async ({ page }) => {\n"
                "  await page.goto('/order/5001/confirmation');\n"
                "  const address = await page.textContent('.shipping-address');\n"
                "  // Old assertion expects single-line format\n"
                "  expect(address).toContain('123 Main St, Apt 4B, New York, NY 10001'); // line 95\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 2: User Dashboard ──
    {
        "id": "user_dashboard",
        "app_description": "SaaS dashboard application — user management and analytics E2E tests via Cypress.",
        "test_summary": {"total": 18, "passed": 13, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_login_with_sso",
                "name": "SSO login redirects through OAuth provider and creates session",
                "category": "environment_issue",
                "error_output": (
                    "CypressError: cy.visit() failed trying to load https://sso.staging.idp.internal/authorize\n"
                    "  Error: ECONNREFUSED - connect ECONNREFUSED 10.1.2.100:443"
                ),
                "stack_trace": (
                    "CypressError: cy.visit() failed\n"
                    "    at visitFailedByErr (cypress/support/commands.js:42:7)\n"
                    "    at cypress/e2e/auth/login.cy.js:15:5"
                ),
                "console_logs": [
                    "[INFO] Initiating SSO redirect to https://sso.staging.idp.internal/authorize",
                    "[ERROR] SSO IdP not reachable: ECONNREFUSED 10.1.2.100:443",
                    "[ERROR] Staging SSO provider is down - ops ticket #OPS-892 filed at 13:45 UTC",
                ],
                "dom_snapshot": '<div class="login-page"><button class="sso-btn">Login with SSO</button><div class="error">SSO provider unavailable</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["ECONNREFUSED", "SSO", "staging", "IdP", "infrastructure", "OPS-892"],
            },
            {
                "test_id": "test_analytics_chart_render",
                "name": "Analytics page renders bar chart with correct data points",
                "category": "flaky_test",
                "error_output": (
                    "AssertionError: Expected 12 bar elements but found 0\n"
                    "  Selector '.chart-bar' matched 0 elements within 4000ms timeout\n"
                    "  at cypress/e2e/analytics/chart.cy.js:38"
                ),
                "stack_trace": (
                    "AssertionError: Timed out retrying after 4000ms\n"
                    "    expected 0 to equal 12\n"
                    "    at Context.eval (cypress/e2e/analytics/chart.cy.js:38:31)"
                ),
                "console_logs": [
                    "[INFO] Fetching analytics data for date range 2026-03-01 to 2026-03-31",
                    "[INFO] API returned 12 data points",
                    "[WARN] Chart.js canvas rendering delayed: requestAnimationFrame took 3800ms on CI runner",
                    "[INFO] Chart render completed at 4200ms (after test timeout)",
                ],
                "dom_snapshot": '<div class="analytics"><canvas id="chart" width="800" height="400"></canvas><div class="chart-loading">Rendering...</div></div>',
                "history": [True, True, False, True, True, False, True, True, False, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "timing", "render", "canvas", "flaky", "CI runner", "slow"],
            },
            {
                "test_id": "test_user_role_permission",
                "name": "Admin user can access user management panel",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected element '.admin-panel' to be visible but it was not found\n"
                    "  User role is 'admin' but panel shows 'Access Denied'\n"
                    "  at cypress/e2e/admin/permissions.cy.js:52"
                ),
                "stack_trace": (
                    "AssertionError: expected '<div.access-denied>' to not exist\n"
                    "    at Context.eval (cypress/e2e/admin/permissions.cy.js:52:18)"
                ),
                "console_logs": [
                    "[INFO] User authenticated: role=admin",
                    "[INFO] Checking permission: user_management.view",
                    "[ERROR] Permission check failed: role 'admin' not found in new RBAC policy v3",
                    "[WARN] RBAC migration incomplete: admin role mapped to 'viewer' in new system",
                ],
                "dom_snapshot": '<div class="dashboard"><div class="access-denied"><h2>Access Denied</h2><p>You do not have permission to view this page.</p></div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["RBAC", "permission", "role mapping", "admin", "regression", "migration"],
            },
            {
                "test_id": "test_export_csv_download",
                "name": "Export button downloads CSV with all user records",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Downloaded file 'users.csv' does not match expected format\n"
                    "  Expected header: 'name,email,role,created_at'\n"
                    "  Actual header:   'full_name,email_address,role,department,created_at,updated_at'\n"
                    "  at cypress/e2e/export/csv.cy.js:27"
                ),
                "stack_trace": (
                    "AssertionError: expected 'full_name,email_address,...' to equal 'name,email,...'\n"
                    "    at Context.eval (cypress/e2e/export/csv.cy.js:27:44)"
                ),
                "console_logs": [
                    "[INFO] CSV export initiated for 150 users",
                    "[INFO] Using new CSV format v2 with expanded columns (JIRA-3456)",
                    "[INFO] File generated: users.csv (150 rows, 6 columns)",
                ],
                "dom_snapshot": '<div class="export"><a href="/downloads/users.csv" class="download-link">Download CSV</a></div>',
                "history": [True, True, True, True, True, False, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["format change", "new columns", "CSV v2", "stale", "outdated assertion", "JIRA-3456"],
            },
            {
                "test_id": "test_notification_bell_count",
                "name": "Notification bell shows unread count badge",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected notification count badge to show '3' but element '.notif-count' shows '0'\n"
                    "  at cypress/e2e/notifications/bell.cy.js:19"
                ),
                "stack_trace": (
                    "AssertionError: expected '0' to equal '3'\n"
                    "    at Context.eval (cypress/e2e/notifications/bell.cy.js:19:38)"
                ),
                "console_logs": [
                    "[INFO] Fetching notifications for user_id=test-user-1",
                    "[INFO] API returned 3 unread notifications",
                    "[ERROR] NotificationBadge: state.count is undefined, defaulting to 0",
                    "[WARN] NotificationProvider context not wrapping NotificationBell component after layout refactor",
                ],
                "dom_snapshot": '<div class="header"><div class="notif-bell"><span class="notif-count">0</span></div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["context", "provider", "undefined", "state", "layout refactor", "regression"],
            },
        ],
        "recent_changes": [
            {
                "commit": "m1n2o3p",
                "author": "tom.dev",
                "message": "Migrate RBAC to policy v3 with granular permissions",
                "files_changed": ["src/auth/rbac.js", "src/auth/policies.json"],
                "diff": (
                    "--- a/src/auth/rbac.js\n"
                    "+++ b/src/auth/rbac.js\n"
                    "@@ -8,6 +8,8 @@\n"
                    " function checkPermission(user, permission) {\n"
                    "-  return LEGACY_ROLES[user.role]?.includes(permission);\n"
                    "+  const policy = loadPolicyV3();\n"
                    "+  return policy.roles[user.role]?.permissions?.includes(permission);\n"
                    "+  // TODO: migrate admin role to policy v3\n"
                    " }\n"
                ),
            },
            {
                "commit": "q4r5s6t",
                "author": "lisa.dev",
                "message": "Refactor layout: move notification bell to new header component",
                "files_changed": ["src/components/Header.jsx", "src/components/NotificationBell.jsx"],
                "diff": (
                    "--- a/src/components/Header.jsx\n"
                    "+++ b/src/components/Header.jsx\n"
                    "@@ -3,7 +3,6 @@\n"
                    " function Header() {\n"
                    "   return (\n"
                    "-    <NotificationProvider>\n"
                    "       <div className='header'>\n"
                    "         <NotificationBell />\n"
                    "       </div>\n"
                    "-    </NotificationProvider>\n"
                    "   );\n"
                    " }\n"
                ),
            },
            {
                "commit": "u7v8w9x",
                "author": "anna.dev",
                "message": "Expand CSV export with new columns for compliance (JIRA-3456)",
                "files_changed": ["src/export/csvGenerator.js"],
                "diff": (
                    "--- a/src/export/csvGenerator.js\n"
                    "+++ b/src/export/csvGenerator.js\n"
                    "@@ -5,4 +5,4 @@\n"
                    "-const COLUMNS = ['name', 'email', 'role', 'created_at'];\n"
                    "+const COLUMNS = ['full_name', 'email_address', 'role', 'department', 'created_at', 'updated_at'];\n"
                ),
            },
        ],
        "source_files": {
            "src/auth/rbac.js": (
                "const policyV3 = require('./policies.json');\n\n"
                "function loadPolicyV3() { return policyV3; }\n\n"
                "function checkPermission(user, permission) {\n"
                "  const policy = loadPolicyV3();\n"
                "  return policy.roles[user.role]?.permissions?.includes(permission);\n"
                "  // TODO: migrate admin role to policy v3\n"
                "}\n\n"
                "module.exports = { checkPermission };\n"
            ),
            "src/components/Header.jsx": (
                "import React from 'react';\n"
                "import NotificationBell from './NotificationBell';\n"
                "// NotificationProvider was here but removed during layout refactor\n\n"
                "function Header() {\n"
                "  return (\n"
                "    <div className='header'>\n"
                "      <NotificationBell />\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default Header;\n"
            ),
            "src/components/NotificationBell.jsx": (
                "import React, { useContext } from 'react';\n"
                "import { NotificationContext } from './NotificationProvider';\n\n"
                "function NotificationBell() {\n"
                "  const ctx = useContext(NotificationContext);\n"
                "  // ctx is undefined when NotificationProvider is missing\n"
                "  return (\n"
                "    <div className='notif-bell'>\n"
                "      <span className='notif-count'>{ctx?.count ?? 0}</span>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default NotificationBell;\n"
            ),
            "src/export/csvGenerator.js": (
                "const COLUMNS = ['full_name', 'email_address', 'role', 'department', 'created_at', 'updated_at'];\n\n"
                "function generateCSV(users) {\n"
                "  const header = COLUMNS.join(',');\n"
                "  const rows = users.map(u => COLUMNS.map(c => u[c] || '').join(','));\n"
                "  return [header, ...rows].join('\\n');\n"
                "}\n\n"
                "module.exports = { generateCSV };\n"
            ),
        },
    },

    # ── Scenario 3: Social Media Feed ──
    {
        "id": "social_feed",
        "app_description": "Social media application — feed, posts, and messaging E2E tests via Selenium.",
        "test_summary": {"total": 30, "passed": 25, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_image_upload_preview",
                "name": "Image upload shows preview thumbnail before posting",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected '.preview-img' src to contain 'blob:' but src was 'undefined'\n"
                    "  at test/e2e/upload.test.js:44"
                ),
                "stack_trace": (
                    "AssertionError: expected 'undefined' to include 'blob:'\n"
                    "    at Context.<anonymous> (test/e2e/upload.test.js:44:26)"
                ),
                "console_logs": [
                    "[INFO] File selected: photo.jpg (2.4MB)",
                    "[ERROR] FileReader.onload: result is null, createObjectURL received null argument",
                    "[WARN] Image preview not generated - FileReader API returned null for uploaded file",
                ],
                "dom_snapshot": '<div class="upload-area"><img class="preview-img" src="undefined" alt="preview"/></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["FileReader", "null", "createObjectURL", "preview", "regression", "upload handler"],
            },
            {
                "test_id": "test_feed_infinite_scroll",
                "name": "Feed loads more posts when user scrolls to bottom",
                "category": "flaky_test",
                "error_output": (
                    "AssertionError: Expected at least 20 post elements but found 10\n"
                    "  Scroll to bottom did not trigger lazy load within 3000ms\n"
                    "  at test/e2e/feed.test.js:67"
                ),
                "stack_trace": (
                    "AssertionError: expected 10 to be at least 20\n"
                    "    at Context.<anonymous> (test/e2e/feed.test.js:67:34)"
                ),
                "console_logs": [
                    "[INFO] Initial feed loaded: 10 posts",
                    "[INFO] Scroll event fired, IntersectionObserver triggered",
                    "[WARN] API response for page 2 took 2800ms (CI runner network latency)",
                    "[INFO] Page 2 data received but DOM update pending when assertion ran",
                ],
                "dom_snapshot": '<div class="feed"><div class="post" data-count="10">...</div><div class="loading-spinner">Loading more...</div></div>',
                "history": [True, False, True, False, True, True, False, True, False, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "scroll", "timing", "lazy load", "flaky", "CI", "network"],
            },
            {
                "test_id": "test_dm_message_send",
                "name": "Direct message is sent and appears in chat window",
                "category": "environment_issue",
                "error_output": (
                    "Error: WebSocket connection to 'wss://chat.staging.internal/ws' failed\n"
                    "  WebSocket is not open: readyState 3 (CLOSED)\n"
                    "  at test/e2e/messaging.test.js:28"
                ),
                "stack_trace": (
                    "Error: WebSocket connection failed\n"
                    "    at WebSocket.onerror (test/e2e/messaging.test.js:28:14)"
                ),
                "console_logs": [
                    "[INFO] Opening WebSocket to wss://chat.staging.internal/ws",
                    "[ERROR] WebSocket CLOSED: readyState=3, code=1006 (abnormal closure)",
                    "[ERROR] Chat microservice unreachable - staging pod evicted due to resource limits",
                ],
                "dom_snapshot": '<div class="chat"><div class="error-banner">Chat service unavailable. Please try again later.</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["WebSocket", "staging", "pod evicted", "infrastructure", "chat service"],
            },
            {
                "test_id": "test_profile_bio_character_limit",
                "name": "Profile bio enforces 500 character limit with counter",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected max character count to be 500 but counter shows '280/1000'\n"
                    "  at test/e2e/profile.test.js:55"
                ),
                "stack_trace": (
                    "AssertionError: expected '280/1000' to contain '500'\n"
                    "    at Context.<anonymous> (test/e2e/profile.test.js:55:30)"
                ),
                "console_logs": [
                    "[INFO] Profile edit page loaded",
                    "[INFO] Bio character limit updated to 1000 per product decision (JIRA-4567)",
                    "[INFO] Character counter showing 280/1000",
                ],
                "dom_snapshot": '<div class="bio-editor"><textarea maxlength="1000">Some bio text...</textarea><span class="char-count">280/1000</span></div>',
                "history": [True, True, True, True, True, True, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["limit change", "1000", "product decision", "stale", "outdated", "JIRA-4567"],
            },
            {
                "test_id": "test_hashtag_link_navigation",
                "name": "Clicking a hashtag navigates to search results for that tag",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected URL to be '/search?tag=javascript' but got '/search?tag='\n"
                    "  Hashtag link href is missing the tag value\n"
                    "  at test/e2e/hashtag.test.js:33"
                ),
                "stack_trace": (
                    "AssertionError: expected '/search?tag=' to equal '/search?tag=javascript'\n"
                    "    at Context.<anonymous> (test/e2e/hashtag.test.js:33:22)"
                ),
                "console_logs": [
                    "[INFO] Post rendered with hashtag #javascript",
                    "[ERROR] Hashtag parser returned empty string: regex match group 1 is undefined",
                    "[WARN] HashtagLink component received tag='' for display text '#javascript'",
                ],
                "dom_snapshot": '<div class="post"><p>Check out <a class="hashtag" href="/search?tag=">#javascript</a></p></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["regex", "parser", "empty string", "hashtag", "bug", "match group"],
            },
        ],
        "recent_changes": [
            {
                "commit": "y1z2a3b",
                "author": "dev.chris",
                "message": "Rewrite image upload to use async FileReader API",
                "files_changed": ["src/upload/imageHandler.js"],
                "diff": (
                    "--- a/src/upload/imageHandler.js\n"
                    "+++ b/src/upload/imageHandler.js\n"
                    "@@ -10,6 +10,7 @@\n"
                    " function handleImageUpload(file) {\n"
                    "-  const url = URL.createObjectURL(file);\n"
                    "-  setPreview(url);\n"
                    "+  const reader = new FileReader();\n"
                    "+  reader.onload = () => setPreview(reader.result);\n"
                    "+  reader.readAsDataURL(null); // BUG: should be reader.readAsDataURL(file)\n"
                    " }\n"
                ),
            },
            {
                "commit": "c4d5e6f",
                "author": "dev.pat",
                "message": "Refactor hashtag parser to use new regex for Unicode support",
                "files_changed": ["src/utils/hashtagParser.js"],
                "diff": (
                    "--- a/src/utils/hashtagParser.js\n"
                    "+++ b/src/utils/hashtagParser.js\n"
                    "@@ -3,4 +3,4 @@\n"
                    "-const HASHTAG_REGEX = /#(\\w+)/g;\n"
                    "+const HASHTAG_REGEX = /#([\\p{L}]+)/gu; // Unicode but missing \\w for alphanumerics\n"
                ),
            },
            {
                "commit": "g7h8i9j",
                "author": "pm.jane",
                "message": "Increase bio character limit to 1000 per product decision (JIRA-4567)",
                "files_changed": ["src/components/ProfileBio.jsx", "src/config/limits.json"],
                "diff": (
                    "--- a/src/config/limits.json\n"
                    "+++ b/src/config/limits.json\n"
                    "@@ -2,3 +2,3 @@\n"
                    '-  "bio_max_length": 500,\n'
                    '+  "bio_max_length": 1000,\n'
                ),
            },
        ],
        "source_files": {
            "src/upload/imageHandler.js": (
                "function handleImageUpload(file) {\n"
                "  const reader = new FileReader();\n"
                "  reader.onload = () => setPreview(reader.result);\n"
                "  reader.readAsDataURL(null); // BUG: passing null instead of file\n"
                "}\n\n"
                "module.exports = { handleImageUpload };\n"
            ),
            "src/utils/hashtagParser.js": (
                "const HASHTAG_REGEX = /#([\\p{L}]+)/gu;\n\n"
                "function parseHashtags(text) {\n"
                "  const tags = [];\n"
                "  let match;\n"
                "  while ((match = HASHTAG_REGEX.exec(text)) !== null) {\n"
                "    tags.push(match[1]); // group 1 may be empty for non-letter chars\n"
                "  }\n"
                "  return tags;\n"
                "}\n\n"
                "module.exports = { parseHashtags };\n"
            ),
            "src/components/ProfileBio.jsx": (
                "import React from 'react';\n"
                "import limits from '../config/limits.json';\n\n"
                "function ProfileBio({ bio, onChange }) {\n"
                "  return (\n"
                "    <div className='bio-editor'>\n"
                "      <textarea maxLength={limits.bio_max_length} value={bio} onChange={onChange} />\n"
                "      <span className='char-count'>{bio.length}/{limits.bio_max_length}</span>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default ProfileBio;\n"
            ),
        },
    },

    # ── Scenario 4: File Manager ──
    {
        "id": "file_manager",
        "app_description": "Cloud file storage application — file upload, sharing, and collaboration E2E tests run via Playwright.",
        "test_summary": {"total": 22, "passed": 17, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_file_version_history",
                "name": "File version history shows correct version count after upload",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected 3 versions in history but found 2\n"
                    "  Latest upload not appearing in version list\n"
                    "  at test/e2e/version.spec.js:38"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/version.spec.js:38:30)"
                ),
                "console_logs": [
                    "[INFO] File 'report.pdf' uploaded: version 3 created (checksum: abc123)",
                    "[INFO] Version dedup check: comparing checksum abc123 against existing versions",
                    "[WARN] VersionTracker.dedup: using '>' instead of '>=' comparison, latest version excluded from count",
                    "[INFO] Version history returned: [v1, v2] (missing v3 due to off-by-one in dedup filter)",
                ],
                "dom_snapshot": '<div class="version-panel"><ul class="version-list"><li>v1 - 2026-04-01</li><li>v2 - 2026-04-03</li></ul><span class="version-count">2 versions</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["off-by-one", "version", "dedup", ">=", "regression", "recent change"],
            },
            {
                "test_id": "test_drag_drop_upload",
                "name": "Drag and drop upload zone accepts files and shows upload progress",
                "category": "flaky_test",
                "error_output": (
                    "TimeoutError: Drop zone '.upload-target' did not receive drop event within 3000ms\n"
                    "  at test/e2e/upload.spec.js:52"
                ),
                "stack_trace": (
                    "TimeoutError: waiting for event 'drop' on '.upload-target'\n"
                    "    at EventHandle.waitForEvent (node_modules/playwright/lib/events.js:89:11)\n"
                    "    at test/e2e/upload.spec.js:52:14"
                ),
                "console_logs": [
                    "[INFO] Drag event started for file 'photo.png'",
                    "[WARN] Simulated dragover event fired but drop zone highlight delayed by 200ms",
                    "[WARN] Drop event dispatched at 2900ms but handler registration completed at 3100ms on CI runner",
                    "[INFO] Upload would have started if drop was registered in time",
                ],
                "dom_snapshot": '<div class="upload-target" data-state="idle"><p>Drag files here to upload</p></div>',
                "history": [True, False, True, True, False, True, False, True, True, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "drag", "drop", "timing", "flaky", "simulated event", "CI"],
            },
            {
                "test_id": "test_share_link_generation",
                "name": "Share button generates a shortened public link for the file",
                "category": "environment_issue",
                "error_output": (
                    "Error: POST https://shorturl.staging.internal/api/shorten failed\n"
                    "  FetchError: connect ECONNREFUSED 10.0.5.22:443\n"
                    "  at test/e2e/share.spec.js:29"
                ),
                "stack_trace": (
                    "FetchError: request to https://shorturl.staging.internal/api/shorten failed\n"
                    "    reason: connect ECONNREFUSED 10.0.5.22:443\n"
                    "    at ClientRequest.<anonymous> (node_modules/node-fetch/lib/index.js:1461:11)\n"
                    "    at test/e2e/share.spec.js:29:20"
                ),
                "console_logs": [
                    "[INFO] Generating share link for file_id=f-2001",
                    "[ERROR] URL shortener service ECONNREFUSED at 10.0.5.22:443",
                    "[ERROR] Staging URL shortener down for scheduled maintenance (ops alert #OPS-1023 at 13:00 UTC)",
                ],
                "dom_snapshot": '<div class="share-dialog"><input class="share-link" value="" placeholder="Generating link..."/><span class="error">Could not generate link</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["ECONNREFUSED", "staging", "URL shortener", "maintenance", "infrastructure", "OPS-1023"],
            },
            {
                "test_id": "test_storage_quota_display",
                "name": "Storage quota bar shows used space and remaining quota",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected quota text to contain '500 MB used' but got '0.5 GB used'\n"
                    "  at test/e2e/quota.spec.js:21"
                ),
                "stack_trace": (
                    "Error: expect(received).toContain(expected)\n"
                    "    at Object.<anonymous> (test/e2e/quota.spec.js:21:34)"
                ),
                "console_logs": [
                    "[INFO] Storage quota loaded: 500MB used of 5GB total",
                    "[INFO] Display format updated to GB per product decision (JIRA-5678)",
                    "[INFO] Rendering quota: '0.5 GB used of 5 GB'",
                ],
                "dom_snapshot": '<div class="quota-bar"><div class="used" style="width:10%"></div><span class="quota-text">0.5 GB used of 5 GB</span></div>',
                "history": [True, True, True, True, True, False, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["format change", "GB", "MB", "product decision", "stale", "outdated", "JIRA-5678"],
            },
            {
                "test_id": "test_folder_rename_sync",
                "name": "Renaming a folder updates breadcrumb paths for all child files",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected breadcrumb to show 'Projects/NewName/doc.pdf'\n"
                    "  but got 'Projects/OldName/doc.pdf'\n"
                    "  at test/e2e/folder.spec.js:44"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/folder.spec.js:44:28)"
                ),
                "console_logs": [
                    "[INFO] Folder renamed: 'OldName' -> 'NewName' (folder_id=d-3001)",
                    "[WARN] PathResolver LRU cache returned stale entry for child file doc.pdf",
                    "[ERROR] Breadcrumb path not updated: cache key 'path:d-3001:doc.pdf' still returns old path. Cache not invalidated on rename.",
                ],
                "dom_snapshot": '<div class="breadcrumb"><span>Projects</span> / <span>OldName</span> / <span>doc.pdf</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["cache invalidation", "breadcrumb", "rename", "path", "regression", "stale cache"],
            },
        ],
        "recent_changes": [
            {
                "commit": "a2b3c4d",
                "author": "alex.dev",
                "message": "Optimize version dedup to skip duplicate checksums",
                "files_changed": ["src/services/versionTracker.js"],
                "diff": (
                    "--- a/src/services/versionTracker.js\n"
                    "+++ b/src/services/versionTracker.js\n"
                    "@@ -20,5 +20,5 @@\n"
                    " function getVersionCount(fileId) {\n"
                    "   const versions = db.getVersions(fileId);\n"
                    "-  return versions.filter(v => v.index >= 0).length;\n"
                    "+  return versions.filter(v => v.index > 0).length; // BUG: excludes version at index 0\n"
                    " }\n"
                ),
            },
            {
                "commit": "e5f6g7h",
                "author": "riley.dev",
                "message": "Refactor path resolver to use LRU cache for breadcrumbs",
                "files_changed": ["src/utils/pathResolver.js"],
                "diff": (
                    "--- a/src/utils/pathResolver.js\n"
                    "+++ b/src/utils/pathResolver.js\n"
                    "@@ -8,6 +8,10 @@\n"
                    "+const pathCache = new LRUCache({ max: 1000 });\n"
                    "+\n"
                    " function resolvePath(folderId, fileName) {\n"
                    "+  const cacheKey = `path:${folderId}:${fileName}`;\n"
                    "+  if (pathCache.has(cacheKey)) return pathCache.get(cacheKey);\n"
                    "   const path = buildPathFromDB(folderId, fileName);\n"
                    "+  pathCache.set(cacheKey, path);\n"
                    "   return path;\n"
                    "+  // NOTE: cache is never invalidated on folder rename\n"
                    " }\n"
                ),
            },
            {
                "commit": "i8j9k0l",
                "author": "pm.jordan",
                "message": "Update storage display to use GB format (JIRA-5678)",
                "files_changed": ["src/components/StorageQuota.jsx", "src/config/display.json"],
                "diff": (
                    "--- a/src/config/display.json\n"
                    "+++ b/src/config/display.json\n"
                    "@@ -3,3 +3,3 @@\n"
                    '-  "storage_unit": "MB",\n'
                    '+  "storage_unit": "GB",\n'
                ),
            },
        ],
        "source_files": {
            "src/services/versionTracker.js": (
                "const db = require('../db/versions');\n\n"
                "function getVersionCount(fileId) {\n"
                "  const versions = db.getVersions(fileId);\n"
                "  return versions.filter(v => v.index > 0).length; // BUG: should be >= 0\n"
                "}\n\n"
                "function addVersion(fileId, checksum) {\n"
                "  const existing = db.getVersions(fileId);\n"
                "  const newIndex = existing.length;\n"
                "  db.insert({ fileId, index: newIndex, checksum });\n"
                "}\n\n"
                "module.exports = { getVersionCount, addVersion };\n"
            ),
            "src/utils/pathResolver.js": (
                "const LRUCache = require('lru-cache');\n"
                "const { buildPathFromDB } = require('../db/folders');\n\n"
                "const pathCache = new LRUCache({ max: 1000 });\n\n"
                "function resolvePath(folderId, fileName) {\n"
                "  const cacheKey = `path:${folderId}:${fileName}`;\n"
                "  if (pathCache.has(cacheKey)) return pathCache.get(cacheKey);\n"
                "  const path = buildPathFromDB(folderId, fileName);\n"
                "  pathCache.set(cacheKey, path);\n"
                "  return path;\n"
                "  // NOTE: cache is never invalidated on folder rename\n"
                "}\n\n"
                "module.exports = { resolvePath };\n"
            ),
            "src/components/StorageQuota.jsx": (
                "import React from 'react';\n"
                "import display from '../config/display.json';\n\n"
                "function StorageQuota({ usedBytes, totalBytes }) {\n"
                "  const divisor = display.storage_unit === 'GB' ? 1e9 : 1e6;\n"
                "  const used = (usedBytes / divisor).toFixed(1);\n"
                "  const total = (totalBytes / divisor).toFixed(0);\n"
                "  return (\n"
                "    <div className='quota-bar'>\n"
                "      <div className='used' style={{ width: `${(usedBytes/totalBytes)*100}%` }} />\n"
                "      <span className='quota-text'>{used} {display.storage_unit} used of {total} {display.storage_unit}</span>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default StorageQuota;\n"
            ),
            "test/e2e/version.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('file version history count', async ({ page }) => {\n"
                "  await page.goto('/files/f-2001/versions');\n"
                "  await page.click('#upload-new-version');\n"
                "  await page.setInputFiles('#file-input', 'fixtures/report-v3.pdf');\n"
                "  await page.waitForSelector('.version-list li', { count: 3 });\n"
                "  const count = await page.textContent('.version-count');\n"
                "  expect(count).toBe('3 versions'); // line 38\n"
                "});\n"
            ),
            "test/e2e/folder.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('folder rename updates child breadcrumbs', async ({ page }) => {\n"
                "  await page.goto('/folders/d-3001');\n"
                "  await page.dblclick('.folder-name');\n"
                "  await page.fill('.folder-name-input', 'NewName');\n"
                "  await page.press('.folder-name-input', 'Enter');\n"
                "  await page.click('.file-row:first-child');\n"
                "  const breadcrumb = await page.textContent('.breadcrumb');\n"
                "  expect(breadcrumb).toBe('Projects/NewName/doc.pdf'); // line 44\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 5: Recipe Platform ──
    {
        "id": "recipe_platform",
        "app_description": "Recipe and meal planning platform — recipe search, meal calendar, and grocery list E2E tests via Cypress.",
        "test_summary": {"total": 20, "passed": 15, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_ingredient_unit_conversion",
                "name": "Unit conversion from cups to milliliters shows correct value",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected '473 mL' but got '472 mL' for 2 cups conversion\n"
                    "  at cypress/e2e/conversion.cy.js:25"
                ),
                "stack_trace": (
                    "AssertionError: expected '472 mL' to equal '473 mL'\n"
                    "    at Context.eval (cypress/e2e/conversion.cy.js:25:30)"
                ),
                "console_logs": [
                    "[INFO] Converting 2 cups to mL",
                    "[INFO] Using conversion constant: 1 cup = 236 mL (truncated from 236.588)",
                    "[WARN] Result: 2 * 236 = 472 mL (expected 473 mL using proper constant 236.588)",
                    "[ERROR] Rounding error from truncated constant: 472 vs expected 473",
                ],
                "dom_snapshot": '<div class="converter"><span class="input">2 cups</span><span class="arrow">=</span><span class="output" data-testid="result">472 mL</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["conversion", "constant", "truncated", "rounding", "236", "regression", "recent change"],
            },
            {
                "test_id": "test_meal_calendar_drag",
                "name": "Dragging a recipe onto a calendar day adds it to the meal plan",
                "category": "flaky_test",
                "error_output": (
                    "AssertionError: Expected '.calendar-day[data-date=\"2026-04-10\"]' to contain '.meal-card' but found 0 elements\n"
                    "  at cypress/e2e/calendar.cy.js:41"
                ),
                "stack_trace": (
                    "AssertionError: expected 0 to be at least 1\n"
                    "    at Context.eval (cypress/e2e/calendar.cy.js:41:28)"
                ),
                "console_logs": [
                    "[INFO] Drag started: recipe 'Pasta Carbonara'",
                    "[INFO] Drop target highlighted: calendar day 2026-04-10",
                    "[WARN] requestAnimationFrame callback delayed 250ms on CI runner, drop event processed late",
                    "[INFO] Meal card added to calendar at 4200ms (after Cypress assertion timeout of 4000ms)",
                ],
                "dom_snapshot": '<div class="calendar-day" data-date="2026-04-10"><div class="drop-indicator active">Drop here</div></div>',
                "history": [True, True, False, True, False, True, True, False, True, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "drag", "animation", "timing", "flaky", "CI", "requestAnimationFrame"],
            },
            {
                "test_id": "test_grocery_list_export",
                "name": "Export grocery list as PDF downloads correctly formatted file",
                "category": "environment_issue",
                "error_output": (
                    "Error: POST https://pdf-renderer.staging.internal/api/render returned 503 Service Unavailable\n"
                    "  at cypress/e2e/grocery.cy.js:33"
                ),
                "stack_trace": (
                    "Error: Request failed with status code 503\n"
                    "    at createError (node_modules/axios/lib/core/createError.js:16:15)\n"
                    "    at cypress/e2e/grocery.cy.js:33:12"
                ),
                "console_logs": [
                    "[INFO] Grocery list compiled: 15 items from 3 recipes",
                    "[INFO] Sending grocery list to PDF renderer for export",
                    "[ERROR] PDF renderer returned 503: staging pod OOMKilled (memory limit 512MB exceeded)",
                    "[ERROR] Staging PDF renderer has been down since 12:30 UTC — ops ticket #OPS-1105",
                ],
                "dom_snapshot": '<div class="export-panel"><button class="export-pdf" disabled>Export PDF</button><span class="error">PDF service unavailable</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["503", "staging", "PDF renderer", "OOM", "infrastructure", "service unavailable"],
            },
            {
                "test_id": "test_recipe_servings_label",
                "name": "Recipe header shows correct servings label",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected text 'Serves: 4' but got '4 servings'\n"
                    "  at cypress/e2e/recipe.cy.js:18"
                ),
                "stack_trace": (
                    "AssertionError: expected '4 servings' to equal 'Serves: 4'\n"
                    "    at Context.eval (cypress/e2e/recipe.cy.js:18:36)"
                ),
                "console_logs": [
                    "[INFO] Recipe loaded: 'Chicken Tikka Masala'",
                    "[INFO] Servings label updated per UX redesign (JIRA-6789): now shows '4 servings' instead of 'Serves: 4'",
                ],
                "dom_snapshot": '<div class="recipe-header"><h1>Chicken Tikka Masala</h1><span class="servings">4 servings</span></div>',
                "history": [True, True, True, True, True, True, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["label change", "UX redesign", "stale", "outdated assertion", "JIRA-6789", "format"],
            },
            {
                "test_id": "test_nutrition_facts_display",
                "name": "Nutrition facts panel shows calorie count for the recipe",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected '.calories' to contain a number but got 'NaN kcal'\n"
                    "  at cypress/e2e/nutrition.cy.js:22"
                ),
                "stack_trace": (
                    "AssertionError: expected 'NaN kcal' to match /^\\d+ kcal$/\n"
                    "    at Context.eval (cypress/e2e/nutrition.cy.js:22:31)"
                ),
                "console_logs": [
                    "[INFO] Loading nutrition data for recipe_id=r-5001",
                    "[WARN] Nutrition API returned null for 'calories' field (recipe has no nutrition data entered)",
                    "[ERROR] NutritionFacts: parseInt(null) returned NaN, displayed 'NaN kcal' — missing null guard removed in refactor",
                ],
                "dom_snapshot": '<div class="nutrition-facts"><div class="calories"><span class="value">NaN</span> kcal</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["NaN", "null check", "calories", "undefined", "regression", "missing guard"],
            },
        ],
        "recent_changes": [
            {
                "commit": "k1l2m3n",
                "author": "chef.dev",
                "message": "Simplify unit conversion constants for readability",
                "files_changed": ["src/utils/unitConversion.js"],
                "diff": (
                    "--- a/src/utils/unitConversion.js\n"
                    "+++ b/src/utils/unitConversion.js\n"
                    "@@ -5,4 +5,4 @@\n"
                    " const CONVERSIONS = {\n"
                    "-  cups_to_ml: 236.588,\n"
                    "+  cups_to_ml: 236, // BUG: truncated, should be 236.588\n"
                    " };\n"
                ),
            },
            {
                "commit": "o4p5q6r",
                "author": "ux.sam",
                "message": "Redesign servings label per UX audit (JIRA-6789)",
                "files_changed": ["src/components/RecipeHeader.jsx"],
                "diff": (
                    "--- a/src/components/RecipeHeader.jsx\n"
                    "+++ b/src/components/RecipeHeader.jsx\n"
                    "@@ -8,3 +8,3 @@\n"
                    "-  <span className='servings'>Serves: {recipe.servings}</span>\n"
                    "+  <span className='servings'>{recipe.servings} servings</span>\n"
                ),
            },
            {
                "commit": "s7t8u9v",
                "author": "dev.nina",
                "message": "Refactor nutrition display component to use new data model",
                "files_changed": ["src/components/NutritionFacts.jsx"],
                "diff": (
                    "--- a/src/components/NutritionFacts.jsx\n"
                    "+++ b/src/components/NutritionFacts.jsx\n"
                    "@@ -6,5 +6,4 @@\n"
                    " function NutritionFacts({ nutrition }) {\n"
                    "-  const calories = nutrition?.calories ?? 0;\n"
                    "+  const calories = parseInt(nutrition.calories); // BUG: no null check, returns NaN when null\n"
                    "   return (\n"
                    "     <div className='nutrition-facts'>\n"
                ),
            },
        ],
        "source_files": {
            "src/utils/unitConversion.js": (
                "const CONVERSIONS = {\n"
                "  cups_to_ml: 236, // should be 236.588\n"
                "  tbsp_to_ml: 14.787,\n"
                "  tsp_to_ml: 4.929,\n"
                "  oz_to_g: 28.3495,\n"
                "};\n\n"
                "function convert(value, fromUnit, toUnit) {\n"
                "  const key = `${fromUnit}_to_${toUnit}`;\n"
                "  if (!CONVERSIONS[key]) throw new Error(`Unknown conversion: ${key}`);\n"
                "  return Math.round(value * CONVERSIONS[key]);\n"
                "}\n\n"
                "module.exports = { convert, CONVERSIONS };\n"
            ),
            "src/components/RecipeHeader.jsx": (
                "import React from 'react';\n\n"
                "function RecipeHeader({ recipe }) {\n"
                "  return (\n"
                "    <div className='recipe-header'>\n"
                "      <h1>{recipe.title}</h1>\n"
                "      <span className='servings'>{recipe.servings} servings</span>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default RecipeHeader;\n"
            ),
            "src/components/NutritionFacts.jsx": (
                "import React from 'react';\n\n"
                "function NutritionFacts({ nutrition }) {\n"
                "  const calories = parseInt(nutrition.calories); // BUG: no null check\n"
                "  return (\n"
                "    <div className='nutrition-facts'>\n"
                "      <div className='calories'>\n"
                "        <span className='value'>{calories}</span> kcal\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n\n"
                "export default NutritionFacts;\n"
            ),
            "cypress/e2e/conversion.cy.js": (
                "describe('Unit Conversion', () => {\n"
                "  it('converts cups to mL correctly', () => {\n"
                "    cy.visit('/tools/converter');\n"
                "    cy.get('#amount').type('2');\n"
                "    cy.get('#from-unit').select('cups');\n"
                "    cy.get('#to-unit').select('mL');\n"
                "    cy.get('[data-testid=\"result\"]').should('have.text', '473 mL'); // line 25\n"
                "  });\n"
                "});\n"
            ),
            "cypress/e2e/recipe.cy.js": (
                "describe('Recipe Page', () => {\n"
                "  it('shows servings label', () => {\n"
                "    cy.visit('/recipes/r-5001');\n"
                "    cy.get('.servings').should('have.text', 'Serves: 4'); // line 18 — stale assertion\n"
                "  });\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 6: Project Tracker ──
    {
        "id": "project_tracker",
        "app_description": "Project management tool — task boards, sprint planning, and team activity E2E tests via Playwright.",
        "test_summary": {"total": 26, "passed": 21, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_sprint_burndown_chart",
                "name": "Sprint burndown chart shows decreasing remaining story points",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected burndown value 20 on day 5 but got 45\n"
                    "  Remaining points should decrease, not increase\n"
                    "  at test/e2e/sprint.spec.js:40"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/sprint.spec.js:40:32)"
                ),
                "console_logs": [
                    "[INFO] Loading burndown data for sprint_id=s-101",
                    "[WARN] SprintMetrics.burndown: SUM(story_points) includes completed items (status=done)",
                    "[ERROR] Burndown value inflated: 45 instead of 20 — completed items double-counted in aggregation query",
                    "[INFO] Query uses SUM(story_points) WHERE status != 'backlog' instead of WHERE status IN ('todo', 'in_progress')",
                ],
                "dom_snapshot": '<div class="burndown-chart"><svg><line class="ideal" /><line class="actual" /><text class="day-5">45 pts remaining</text></svg></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["burndown", "SUM", "aggregation", "completed", "double-counted", "regression", "query"],
            },
            {
                "test_id": "test_kanban_card_move",
                "name": "Moving a card between kanban columns updates its status",
                "category": "flaky_test",
                "error_output": (
                    "AssertionError: Expected card 'TASK-42' to be in column 'In Progress' but found it in 'To Do'\n"
                    "  at test/e2e/kanban.spec.js:55"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/kanban.spec.js:55:26)"
                ),
                "console_logs": [
                    "[INFO] Drag started: card TASK-42 from column 'To Do'",
                    "[INFO] Drop target: column 'In Progress'",
                    "[WARN] sortable.js transition animation took 350ms, assertion ran at 300ms before DOM settled",
                    "[INFO] Card TASK-42 moved to 'In Progress' at 400ms (after assertion failed)",
                ],
                "dom_snapshot": '<div class="kanban"><div class="column" data-status="todo"><div class="card" data-id="TASK-42">TASK-42</div></div><div class="column" data-status="in_progress"></div></div>',
                "history": [True, False, True, True, False, True, False, True, True, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "sortable", "animation", "timing", "flaky", "drag", "transition"],
            },
            {
                "test_id": "test_team_activity_feed",
                "name": "Team activity feed shows real-time updates via WebSocket",
                "category": "environment_issue",
                "error_output": (
                    "Error: WebSocket connection to 'wss://events.staging.internal/stream' failed\n"
                    "  ECONNREFUSED 10.0.8.15:443\n"
                    "  at test/e2e/activity.spec.js:29"
                ),
                "stack_trace": (
                    "Error: WebSocket connection failed\n"
                    "    at WebSocket.onerror (test/e2e/activity.spec.js:29:16)"
                ),
                "console_logs": [
                    "[INFO] Connecting to activity feed: wss://events.staging.internal/stream",
                    "[ERROR] WebSocket ECONNREFUSED 10.0.8.15:443",
                    "[ERROR] Staging event stream service blocked by firewall rule change (ops ticket #OPS-1150)",
                ],
                "dom_snapshot": '<div class="activity-feed"><div class="error-banner">Activity feed unavailable</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["WebSocket", "staging", "firewall", "ECONNREFUSED", "infrastructure", "event stream"],
            },
            {
                "test_id": "test_task_priority_badge",
                "name": "Task card displays correct priority badge",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected '.priority-badge' text to be 'High' but element contains no text\n"
                    "  Badge is now icon-only per design system update\n"
                    "  at test/e2e/task.spec.js:36"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/task.spec.js:36:30)"
                ),
                "console_logs": [
                    "[INFO] Task TASK-42 loaded with priority: high",
                    "[INFO] Priority badge rendered as icon-only (design system v3, JIRA-7890)",
                    "[INFO] Badge uses aria-label='High priority' instead of visible text",
                ],
                "dom_snapshot": '<div class="task-card"><span class="priority-badge priority-high" aria-label="High priority"><svg class="icon-priority-high"/></span></div>',
                "history": [True, True, True, True, True, False, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["design system", "icon", "badge", "stale", "outdated assertion", "JIRA-7890", "text to icon"],
            },
            {
                "test_id": "test_sprint_velocity_calc",
                "name": "Sprint velocity chart shows correct average across completed sprints",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected average velocity 30 but got 42\n"
                    "  Cancelled sprint points should not be included\n"
                    "  at test/e2e/velocity.spec.js:28"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/velocity.spec.js:28:33)"
                ),
                "console_logs": [
                    "[INFO] Calculating velocity for team_id=t-201",
                    "[WARN] Sprint filter: status != 'draft' includes cancelled sprints (s-098: cancelled, 55 pts)",
                    "[ERROR] Velocity inflated: 42 avg instead of 30 — filter should be status == 'completed' not status != 'draft'",
                ],
                "dom_snapshot": '<div class="velocity-chart"><span class="avg-velocity">Avg: 42 pts/sprint</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["velocity", "cancelled", "filter", "status", "regression", "query", "recent change"],
            },
        ],
        "recent_changes": [
            {
                "commit": "w1x2y3z",
                "author": "lead.dev",
                "message": "Refactor sprint metrics queries for performance",
                "files_changed": ["src/services/sprintMetrics.js"],
                "diff": (
                    "--- a/src/services/sprintMetrics.js\n"
                    "+++ b/src/services/sprintMetrics.js\n"
                    "@@ -15,7 +15,7 @@\n"
                    " function getBurndownData(sprintId) {\n"
                    "   const tasks = db.query(\n"
                    "-    'SELECT SUM(story_points) FROM tasks WHERE sprint_id = ? AND status IN (?, ?)',\n"
                    "-    [sprintId, 'todo', 'in_progress']\n"
                    "+    'SELECT SUM(story_points) FROM tasks WHERE sprint_id = ? AND status != ?',\n"
                    "+    [sprintId, 'backlog'] // BUG: includes 'done' status\n"
                    "   );\n"
                    " }\n"
                    "@@ -30,7 +30,7 @@\n"
                    " function getVelocity(teamId) {\n"
                    "   const sprints = db.query(\n"
                    "-    'SELECT AVG(completed_points) FROM sprints WHERE team_id = ? AND status = ?',\n"
                    "-    [teamId, 'completed']\n"
                    "+    'SELECT AVG(completed_points) FROM sprints WHERE team_id = ? AND status != ?',\n"
                    "+    [teamId, 'draft'] // BUG: includes 'cancelled' sprints\n"
                    "   );\n"
                    " }\n"
                ),
            },
            {
                "commit": "a4b5c6d",
                "author": "design.lead",
                "message": "Migrate priority badges to icon-only design (JIRA-7890)",
                "files_changed": ["src/components/PriorityBadge.jsx", "src/styles/badges.css"],
                "diff": (
                    "--- a/src/components/PriorityBadge.jsx\n"
                    "+++ b/src/components/PriorityBadge.jsx\n"
                    "@@ -4,5 +4,7 @@\n"
                    " function PriorityBadge({ priority }) {\n"
                    "-  return <span className={`priority-badge priority-${priority}`}>{capitalize(priority)}</span>;\n"
                    "+  return (\n"
                    "+    <span className={`priority-badge priority-${priority}`} aria-label={`${capitalize(priority)} priority`}>\n"
                    "+      <PriorityIcon level={priority} />\n"
                    "+    </span>\n"
                    "+  );\n"
                    " }\n"
                ),
            },
            {
                "commit": "e7f8g9h",
                "author": "backend.dev",
                "message": "Add sprint status filter to velocity endpoint",
                "files_changed": ["src/api/velocity.js"],
                "diff": (
                    "--- a/src/api/velocity.js\n"
                    "+++ b/src/api/velocity.js\n"
                    "@@ -10,5 +10,6 @@\n"
                    " router.get('/api/velocity/:teamId', async (req, res) => {\n"
                    "   const { teamId } = req.params;\n"
                    "+  // Uses updated sprintMetrics.getVelocity which now filters by status != 'draft'\n"
                    "   const velocity = await sprintMetrics.getVelocity(teamId);\n"
                    "   res.json({ average: velocity });\n"
                    " });\n"
                ),
            },
        ],
        "source_files": {
            "src/services/sprintMetrics.js": (
                "const db = require('../db');\n\n"
                "function getBurndownData(sprintId) {\n"
                "  const result = db.query(\n"
                "    'SELECT SUM(story_points) FROM tasks WHERE sprint_id = ? AND status != ?',\n"
                "    [sprintId, 'backlog'] // BUG: includes 'done', should be status IN ('todo', 'in_progress')\n"
                "  );\n"
                "  return result;\n"
                "}\n\n"
                "function getVelocity(teamId) {\n"
                "  const result = db.query(\n"
                "    'SELECT AVG(completed_points) FROM sprints WHERE team_id = ? AND status != ?',\n"
                "    [teamId, 'draft'] // BUG: includes 'cancelled', should be status = 'completed'\n"
                "  );\n"
                "  return result;\n"
                "}\n\n"
                "module.exports = { getBurndownData, getVelocity };\n"
            ),
            "src/components/PriorityBadge.jsx": (
                "import React from 'react';\n"
                "import { PriorityIcon } from './icons';\n\n"
                "function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }\n\n"
                "function PriorityBadge({ priority }) {\n"
                "  return (\n"
                "    <span className={`priority-badge priority-${priority}`} aria-label={`${capitalize(priority)} priority`}>\n"
                "      <PriorityIcon level={priority} />\n"
                "    </span>\n"
                "  );\n"
                "}\n\n"
                "export default PriorityBadge;\n"
            ),
            "src/api/velocity.js": (
                "const express = require('express');\n"
                "const sprintMetrics = require('../services/sprintMetrics');\n"
                "const router = express.Router();\n\n"
                "router.get('/api/velocity/:teamId', async (req, res) => {\n"
                "  const { teamId } = req.params;\n"
                "  const velocity = await sprintMetrics.getVelocity(teamId);\n"
                "  res.json({ average: velocity });\n"
                "});\n\n"
                "module.exports = router;\n"
            ),
            "test/e2e/sprint.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('burndown chart shows decreasing points', async ({ page }) => {\n"
                "  await page.goto('/sprints/s-101/burndown');\n"
                "  const day5 = await page.textContent('.day-5');\n"
                "  expect(parseInt(day5)).toBe(20); // line 40\n"
                "});\n"
            ),
            "test/e2e/kanban.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('move card between columns', async ({ page }) => {\n"
                "  await page.goto('/boards/b-301');\n"
                "  await page.dragAndDrop('[data-id=\"TASK-42\"]', '[data-status=\"in_progress\"]');\n"
                "  const column = await page.getAttribute('[data-id=\"TASK-42\"]', 'data-column');\n"
                "  expect(column).toBe('in_progress'); // line 55 — flaky on CI\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 7: Analytics Dashboard ──
    {
        "id": "analytics_dashboard",
        "app_description": "Analytics dashboard — real-time charts, data aggregation, and report generation E2E tests run on every PR via Playwright.",
        "test_summary": {"total": 28, "passed": 23, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_chart_data_aggregation",
                "name": "Chart displays correct aggregated totals for selected metrics",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected total revenue to be $142,500 but got $128,300\n"
                    "  Missing $14,200 from rows where 'amount' column is NULL\n"
                    "  at test/e2e/chart.spec.js:53"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/chart.spec.js:53:32)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)\n"
                    "    at resolve (node_modules/jest/build/jasmine.js:64:11)"
                ),
                "console_logs": [
                    "[INFO] Loading chart data for metric: revenue, period: Q1-2026",
                    "[INFO] Query: SELECT SUM(amount) FROM transactions WHERE period = 'Q1-2026'",
                    "[WARN] SUM returned 128300 but expected 142500 — 47 rows have NULL amount after migration 0042_add_nullable_amount",
                    "[ERROR] Aggregation mismatch: NULL values excluded from SUM instead of treated as 0",
                ],
                "dom_snapshot": '<div class="chart-container"><div class="chart-total" data-testid="metric-total">$128,300</div><canvas id="revenue-chart" width="960" height="480"></canvas></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["null", "aggregation", "SUM", "migration", "nullable", "recent change"],
            },
            {
                "test_id": "test_date_range_filter",
                "name": "Date range filter returns only data within selected start and end dates",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected 15 results within 2026-03-01 to 2026-03-31 but got 18\n"
                    "  3 extra results have timestamps on 2026-04-01 00:xx UTC (local timezone offset issue)\n"
                    "  at test/e2e/filters.spec.js:71"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/filters.spec.js:71:28)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)"
                ),
                "console_logs": [
                    "[INFO] Date range filter applied: 2026-03-01 to 2026-03-31",
                    "[INFO] Query executed with WHERE created_at >= '2026-03-01' AND created_at < '2026-04-01'",
                    "[WARN] 3 records returned with created_at='2026-04-01T00:15:00Z' — UTC vs America/New_York offset mismatch",
                    "[ERROR] Date boundary conversion uses local timezone instead of UTC for comparison",
                ],
                "dom_snapshot": '<div class="filter-panel"><input type="date" value="2026-03-01" /><input type="date" value="2026-03-31" /><span class="result-count">18 results</span></div>',
                "history": [True, True, True, True, True, True, True, True, False, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["timezone", "UTC", "offset", "date range", "conversion", "regression"],
            },
            {
                "test_id": "test_realtime_chart_update",
                "name": "Real-time chart updates when new data arrives via WebSocket",
                "category": "flaky_test",
                "error_output": (
                    "TimeoutError: Waiting for chart data point count to increase from 10 to 11 exceeded 5000ms\n"
                    "  WebSocket message received at 4900ms but DOM update was not reflected\n"
                    "  at test/e2e/realtime.spec.js:45"
                ),
                "stack_trace": (
                    "TimeoutError: waiting for condition\n"
                    "    at waitForFunction (node_modules/playwright/lib/frames.js:210:15)\n"
                    "    at test/e2e/realtime.spec.js:45:22"
                ),
                "console_logs": [
                    "[INFO] WebSocket connected to wss://analytics-ws.staging.internal/stream",
                    "[INFO] Listening for real-time data updates on channel: revenue",
                    "[WARN] WebSocket message received after 4900ms — close to 5000ms assertion timeout",
                    "[INFO] Chart DOM updated at 5100ms — 100ms after assertion timeout",
                ],
                "dom_snapshot": '<div class="realtime-chart"><canvas id="live-chart"></canvas><span class="data-points">10 points</span><span class="ws-status">Connected</span></div>',
                "history": [True, False, True, True, False, True, True, False, True, False],
                "recommendation": "rerun",
                "evidence_keywords": ["intermittent", "WebSocket", "timing", "race condition", "inconsistent", "flaky"],
            },
            {
                "test_id": "test_export_csv_download",
                "name": "Export CSV button downloads report file to local disk",
                "category": "environment_issue",
                "error_output": (
                    "Error: Request to https://file-storage.staging.internal/v1/export failed\n"
                    "  FetchError: connect ECONNREFUSED 10.0.5.88:443\n"
                    "  at test/e2e/export.spec.js:29"
                ),
                "stack_trace": (
                    "FetchError: request to https://file-storage.staging.internal/v1/export failed\n"
                    "    reason: connect ECONNREFUSED 10.0.5.88:443\n"
                    "    at ClientRequest.<anonymous> (node_modules/node-fetch/lib/index.js:1461:11)\n"
                    "    at test/e2e/export.spec.js:29:18"
                ),
                "console_logs": [
                    "[INFO] CSV export requested for report: Q1-2026 Revenue",
                    "[INFO] Generating CSV via file-storage service at https://file-storage.staging.internal/v1/export",
                    "[ERROR] file-storage.staging.internal:443 - ECONNREFUSED",
                    "[ERROR] Staging file storage service is down — ops alert #SRE-1104 triggered at 09:12 UTC",
                ],
                "dom_snapshot": '<div class="export-panel"><button class="export-btn" disabled>Export CSV</button><div class="error-toast">File storage service unavailable</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["staging", "file storage", "ECONNREFUSED", "infrastructure", "download", "service down"],
            },
            {
                "test_id": "test_legacy_pie_chart_render",
                "name": "Legacy pie chart renders with correct segment colors and labels",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected element '.pie-chart-segment' to exist but found 0 matches\n"
                    "  Component class was renamed from 'pie-chart-segment' to 'donut-segment' in UI refactor\n"
                    "  at test/e2e/pie-chart.spec.js:38"
                ),
                "stack_trace": (
                    "Error: expect(received).toBeGreaterThan(0)\n"
                    "    at Object.<anonymous> (test/e2e/pie-chart.spec.js:38:46)"
                ),
                "console_logs": [
                    "[INFO] Rendering chart type: donut (migrated from pie)",
                    "[INFO] Component PieChart renamed to DonutChart 3 weeks ago (PR #847)",
                    "[WARN] CSS class .pie-chart-segment no longer exists — replaced by .donut-segment",
                ],
                "dom_snapshot": '<div class="chart-wrapper"><svg class="donut-chart"><path class="donut-segment" d="M10,80 A70,70 0 0,1 80,10" fill="#4CAF50"/><path class="donut-segment" d="M80,10 A70,70 0 0,1 150,80" fill="#FF9800"/></svg></div>',
                "history": [False, False, False, False, False, False, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["outdated", "renamed", "class name", "refactor", "stale", "always fails"],
            },
        ],
        "recent_changes": [
            {
                "commit": "f8a2c1d",
                "author": "priya.dev",
                "message": "Add nullable amount column to transactions table (migration 0042)",
                "files_changed": ["src/db/migrations/0042_add_nullable_amount.sql", "src/services/aggregation.js"],
                "diff": (
                    "--- a/src/services/aggregation.js\n"
                    "+++ b/src/services/aggregation.js\n"
                    "@@ -12,6 +12,7 @@\n"
                    " async function getTotal(metric, period) {\n"
                    "   const query = `SELECT SUM(amount) AS total FROM transactions WHERE period = $1`;\n"
                    "-  // amount was NOT NULL, SUM always correct\n"
                    "+  // amount is now nullable after migration 0042\n"
                    "+  // BUG: SUM ignores NULL rows — should use COALESCE(amount, 0)\n"
                    "   const result = await db.query(query, [period]);\n"
                    "   return result.rows[0].total;\n"
                    " }\n"
                ),
            },
            {
                "commit": "b3e7d9f",
                "author": "carlos.dev",
                "message": "Fix date range filter to use server timestamps consistently",
                "files_changed": ["src/filters/dateRange.js"],
                "diff": (
                    "--- a/src/filters/dateRange.js\n"
                    "+++ b/src/filters/dateRange.js\n"
                    "@@ -7,5 +7,5 @@\n"
                    " function buildDateFilter(start, end) {\n"
                    "-  const startUTC = new Date(start).toISOString();\n"
                    "-  const endUTC = new Date(end).toISOString();\n"
                    "+  const startUTC = new Date(start).toLocaleDateString(); // BUG: uses local timezone\n"
                    "+  const endUTC = new Date(end).toLocaleDateString();     // BUG: should be toISOString()\n"
                    "   return { start: startUTC, end: endUTC };\n"
                    " }\n"
                ),
            },
            {
                "commit": "d5f1a4e",
                "author": "nina.dev",
                "message": "Refactor pie chart to donut chart with new component library (PR #847)",
                "files_changed": ["src/components/DonutChart.jsx", "src/components/PieChart.jsx"],
                "diff": (
                    "--- a/src/components/PieChart.jsx\n"
                    "+++ /dev/null\n"
                    "@@ -1,15 +0,0 @@\n"
                    "-import React from 'react';\n"
                    "-function PieChart({ data }) {\n"
                    "-  return <svg className='pie-chart'>...</svg>;\n"
                    "-}\n"
                    "--- /dev/null\n"
                    "+++ b/src/components/DonutChart.jsx\n"
                    "@@ -0,0 +1,18 @@\n"
                    "+import React from 'react';\n"
                    "+function DonutChart({ data }) {\n"
                    "+  return (\n"
                    "+    <svg className='donut-chart'>\n"
                    "+      {data.map(seg => <path className='donut-segment' ... />)}\n"
                    "+    </svg>\n"
                    "+  );\n"
                    "+}\n"
                ),
            },
        ],
        "source_files": {
            "src/services/aggregation.js": (
                "const db = require('../db/connection');\n\n"
                "async function getTotal(metric, period) {\n"
                "  const query = `SELECT SUM(amount) AS total FROM transactions WHERE period = $1`;\n"
                "  // amount is now nullable after migration 0042\n"
                "  // SUM ignores NULL rows — should use COALESCE(amount, 0)\n"
                "  const result = await db.query(query, [period]);\n"
                "  return result.rows[0].total;\n"
                "}\n\n"
                "module.exports = { getTotal };\n"
            ),
            "src/filters/dateRange.js": (
                "function buildDateFilter(start, end) {\n"
                "  const startUTC = new Date(start).toLocaleDateString(); // BUG: should be toISOString()\n"
                "  const endUTC = new Date(end).toLocaleDateString();     // BUG: should be toISOString()\n"
                "  return { start: startUTC, end: endUTC };\n"
                "}\n\n"
                "module.exports = { buildDateFilter };\n"
            ),
            "src/components/DonutChart.jsx": (
                "import React from 'react';\n\n"
                "function DonutChart({ data }) {\n"
                "  return (\n"
                "    <svg className='donut-chart'>\n"
                "      {data.map((seg, i) => (\n"
                "        <path key={i} className='donut-segment' d={seg.path} fill={seg.color} />\n"
                "      ))}\n"
                "    </svg>\n"
                "  );\n"
                "}\n\n"
                "export default DonutChart;\n"
            ),
            "test/e2e/chart.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('chart data aggregation shows correct total', async ({ page }) => {\n"
                "  await page.goto('/analytics/revenue?period=Q1-2026');\n"
                "  await page.waitForSelector('[data-testid=\"metric-total\"]');\n"
                "  const total = await page.textContent('[data-testid=\"metric-total\"]');\n"
                "  expect(total).toBe('$142,500'); // line 53\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 8: Notification Center ──
    {
        "id": "notification_center",
        "app_description": "Notification center — WebSocket delivery, email templates, push notifications, and preference management E2E tests.",
        "test_summary": {"total": 22, "passed": 17, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_email_template_render",
                "name": "Email template renders with all user variables populated",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected email body to contain 'Hello, Alice' but got 'Hello, undefined'\n"
                    "  Template variable {{user.first_name}} is undefined after field rename\n"
                    "  at test/e2e/email-template.spec.js:34"
                ),
                "stack_trace": (
                    "Error: expect(received).toContain(expected)\n"
                    "    at Object.<anonymous> (test/e2e/email-template.spec.js:34:31)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)"
                ),
                "console_logs": [
                    "[INFO] Rendering email template: welcome_email for user_id=u-5001",
                    "[INFO] Template context: {user: {name: 'Alice Johnson', email: 'alice@example.com'}}",
                    "[WARN] Template variable 'user.first_name' resolved to undefined — field was renamed to 'user.name'",
                    "[ERROR] Email body contains 'Hello, undefined' — template not updated after user model refactor",
                ],
                "dom_snapshot": '<div class="email-preview"><div class="email-body"><p>Hello, undefined</p><p>Welcome to our platform!</p></div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["template", "variable", "undefined", "renamed", "user field", "regression"],
            },
            {
                "test_id": "test_push_notification_delivery",
                "name": "Push notification payload is delivered to device endpoint",
                "category": "genuine_bug",
                "error_output": (
                    "Error: Push notification payload size 4,312 bytes exceeds 4,096 byte limit\n"
                    "  PayloadTooLargeError: FCM rejects payloads > 4KB\n"
                    "  at test/e2e/push-notification.spec.js:48"
                ),
                "stack_trace": (
                    "PayloadTooLargeError: Payload size 4312 exceeds limit 4096\n"
                    "    at validatePayload (src/notifications/push.js:28:11)\n"
                    "    at sendPush (src/notifications/push.js:45:5)\n"
                    "    at test/e2e/push-notification.spec.js:48:22"
                ),
                "console_logs": [
                    "[INFO] Building push notification for event: new_message",
                    "[INFO] Payload includes fields: title, body, icon, badge, data.sender, data.preview, data.actions, data.deepLink",
                    "[WARN] Payload size: 4312 bytes (limit: 4096 bytes) — exceeded after adding data.actions and data.deepLink",
                    "[ERROR] FCM rejected payload: PayloadTooLargeError — notification not delivered",
                ],
                "dom_snapshot": '<div class="push-config"><span class="payload-size">4,312 bytes</span><span class="limit">4,096 bytes</span><span class="status error">Rejected</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["payload", "size", "4KB", "limit", "exceeded", "new fields", "regression"],
            },
            {
                "test_id": "test_websocket_reconnection",
                "name": "WebSocket reconnects automatically after connection drop",
                "category": "flaky_test",
                "error_output": (
                    "TimeoutError: WebSocket did not reconnect within 8000ms after simulated disconnect\n"
                    "  Reconnect attempt observed at 7500ms but handshake completed at 8200ms\n"
                    "  at test/e2e/ws-reconnect.spec.js:62"
                ),
                "stack_trace": (
                    "TimeoutError: waiting for WebSocket readyState to become OPEN\n"
                    "    at waitForCondition (node_modules/playwright/lib/frames.js:210:15)\n"
                    "    at test/e2e/ws-reconnect.spec.js:62:20"
                ),
                "console_logs": [
                    "[INFO] WebSocket connected to wss://notif.staging.internal/ws",
                    "[INFO] Simulating connection drop (readyState -> CLOSED)",
                    "[WARN] Reconnect backoff: attempt 1 at 2000ms, attempt 2 at 4000ms, attempt 3 at 7500ms",
                    "[INFO] Reconnect handshake completed at 8200ms — 200ms after assertion timeout",
                ],
                "dom_snapshot": '<div class="ws-status"><span class="indicator reconnecting">Reconnecting...</span><span class="attempt">Attempt 3/5</span></div>',
                "history": [True, False, True, False, True, True, False, True, True, False],
                "recommendation": "rerun",
                "evidence_keywords": ["reconnect", "timing", "WebSocket", "intermittent", "race condition"],
            },
            {
                "test_id": "test_sms_gateway_integration",
                "name": "SMS notification is sent via gateway and delivery receipt received",
                "category": "environment_issue",
                "error_output": (
                    "Error: POST https://sms-gateway.sandbox.twilio.com/v1/messages returned 401 Unauthorized\n"
                    "  AuthenticationError: Invalid credentials — sandbox API key expired\n"
                    "  at test/e2e/sms-gateway.spec.js:25"
                ),
                "stack_trace": (
                    "AuthenticationError: 401 Unauthorized\n"
                    "    at SMSClient.send (src/notifications/smsClient.js:18:11)\n"
                    "    at test/e2e/sms-gateway.spec.js:25:28"
                ),
                "console_logs": [
                    "[INFO] Sending SMS via sandbox gateway to +1-555-0199",
                    "[ERROR] SMS gateway returned 401: 'API key expired on 2026-04-01. Rotate credentials in vault.'",
                    "[ERROR] Sandbox credentials last rotated: 2026-01-01 — expired after 90-day TTL",
                    "[WARN] SMS delivery failed — check credential rotation schedule in ops vault",
                ],
                "dom_snapshot": '<div class="sms-status"><span class="delivery-status error">Authentication Failed</span><span class="error-code">401</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["credentials", "expired", "sandbox", "SMS gateway", "401", "authentication"],
            },
            {
                "test_id": "test_notification_badge_count",
                "name": "Notification badge displays correct count of pending items",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected badge count to be 7 (total) but got 3 (unread only)\n"
                    "  Badge logic changed from total notifications to unread-only 2 sprints ago\n"
                    "  at test/e2e/badge.spec.js:41"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/badge.spec.js:41:34)"
                ),
                "console_logs": [
                    "[INFO] Fetching notification count for user_id=u-3001",
                    "[INFO] API returned: {total: 7, unread: 3, read: 4}",
                    "[INFO] Badge component renders unread count: 3 (changed from total in sprint 22, JIRA-5890)",
                ],
                "dom_snapshot": '<div class="notif-header"><span class="badge-count" data-testid="badge">3</span></div>',
                "history": [False, False, False, False, False, False, True, True, True, True],
                "recommendation": "update_test",
                "evidence_keywords": ["outdated", "badge count", "unread", "logic changed", "stale"],
            },
        ],
        "recent_changes": [
            {
                "commit": "a9c4e2b",
                "author": "raj.dev",
                "message": "Rename user.first_name to user.name in user model (JIRA-5721)",
                "files_changed": ["src/models/user.js", "src/templates/welcome_email.hbs"],
                "diff": (
                    "--- a/src/models/user.js\n"
                    "+++ b/src/models/user.js\n"
                    "@@ -5,4 +5,4 @@\n"
                    " const userSchema = {\n"
                    "-  first_name: { type: String, required: true },\n"
                    "-  last_name: { type: String, required: true },\n"
                    "+  name: { type: String, required: true },  // consolidated first + last\n"
                    "   email: { type: String, required: true },\n"
                    " };\n"
                    "--- a/src/templates/welcome_email.hbs\n"
                    "+++ b/src/templates/welcome_email.hbs\n"
                    "@@ -1,3 +1,3 @@\n"
                    "-<p>Hello, {{user.first_name}}</p>\n"
                    "+<p>Hello, {{user.first_name}}</p>  {{!-- BUG: should be user.name --}}\n"
                ),
            },
            {
                "commit": "c7f1d8a",
                "author": "mei.dev",
                "message": "Add deep link and action buttons to push notification payload",
                "files_changed": ["src/notifications/push.js"],
                "diff": (
                    "--- a/src/notifications/push.js\n"
                    "+++ b/src/notifications/push.js\n"
                    "@@ -18,6 +18,10 @@\n"
                    " function buildPayload(event, data) {\n"
                    "   const payload = {\n"
                    "     title: event.title,\n"
                    "     body: event.body,\n"
                    "     icon: event.icon,\n"
                    "+    data: {\n"
                    "+      ...data,\n"
                    "+      actions: JSON.stringify(event.actions),  // adds ~200 bytes\n"
                    "+      deepLink: event.deepLink,                // adds ~150 bytes\n"
                    "+    },\n"
                    "   };\n"
                    "+  // Total payload now exceeds 4KB FCM limit\n"
                    "   return payload;\n"
                    " }\n"
                ),
            },
            {
                "commit": "e2b6a3d",
                "author": "sam.dev",
                "message": "Switch notification badge from total count to unread-only (JIRA-5890)",
                "files_changed": ["src/components/NotificationBadge.jsx"],
                "diff": (
                    "--- a/src/components/NotificationBadge.jsx\n"
                    "+++ b/src/components/NotificationBadge.jsx\n"
                    "@@ -8,4 +8,4 @@\n"
                    " function NotificationBadge({ notifications }) {\n"
                    "-  const count = notifications.total;\n"
                    "+  const count = notifications.unread; // show unread only per JIRA-5890\n"
                    "   return <span className='badge-count' data-testid='badge'>{count}</span>;\n"
                    " }\n"
                ),
            },
        ],
        "source_files": {
            "src/templates/welcome_email.hbs": (
                "<html>\n"
                "<body>\n"
                "  <p>Hello, {{user.first_name}}</p>\n"
                "  <!-- BUG: user.first_name was renamed to user.name -->\n"
                "  <p>Welcome to our platform!</p>\n"
                "  <p>Your account ({{user.email}}) is ready.</p>\n"
                "</body>\n"
                "</html>\n"
            ),
            "src/notifications/push.js": (
                "const FCM_PAYLOAD_LIMIT = 4096;\n\n"
                "function validatePayload(payload) {\n"
                "  const size = Buffer.byteLength(JSON.stringify(payload));\n"
                "  if (size > FCM_PAYLOAD_LIMIT) {\n"
                "    throw new PayloadTooLargeError(`Payload size ${size} exceeds limit ${FCM_PAYLOAD_LIMIT}`);\n"
                "  }\n"
                "}\n\n"
                "function buildPayload(event, data) {\n"
                "  const payload = {\n"
                "    title: event.title,\n"
                "    body: event.body,\n"
                "    icon: event.icon,\n"
                "    data: {\n"
                "      ...data,\n"
                "      actions: JSON.stringify(event.actions),\n"
                "      deepLink: event.deepLink,\n"
                "    },\n"
                "  };\n"
                "  return payload;\n"
                "}\n\n"
                "module.exports = { buildPayload, validatePayload };\n"
            ),
            "src/components/NotificationBadge.jsx": (
                "import React from 'react';\n\n"
                "function NotificationBadge({ notifications }) {\n"
                "  const count = notifications.unread; // show unread only per JIRA-5890\n"
                "  return <span className='badge-count' data-testid='badge'>{count}</span>;\n"
                "}\n\n"
                "export default NotificationBadge;\n"
            ),
            "test/e2e/email-template.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('email template renders user name', async ({ page }) => {\n"
                "  await page.goto('/admin/templates/preview/welcome_email?user=u-5001');\n"
                "  const body = await page.textContent('.email-body');\n"
                "  expect(body).toContain('Hello, Alice'); // line 34\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 9: Search Engine ──
    {
        "id": "search_engine",
        "app_description": "Search engine — full-text search, faceted filters, autocomplete, and relevance scoring E2E tests.",
        "test_summary": {"total": 20, "passed": 15, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_search_relevance_scoring",
                "name": "Search results are ranked by relevance score in descending order",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected first result to be 'Python Tutorial' (score 0.95) but got 'Cooking Basics' (score 0.42)\n"
                    "  Relevance scoring boosting weights were changed in recent commit\n"
                    "  at test/e2e/search-relevance.spec.js:39"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/search-relevance.spec.js:39:30)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)"
                ),
                "console_logs": [
                    "[INFO] Search query: 'python programming' executed against index 'articles'",
                    "[INFO] Boosting weights applied: title=5.0, body=1.0, tags=3.0 (changed from title=2.0, body=1.0, tags=1.0)",
                    "[WARN] Result #1: 'Cooking Basics' (score=0.42, boosted by tag match 'basics') — expected 'Python Tutorial'",
                    "[ERROR] Relevance scoring regression: title boost too high relative to exact-match body content",
                ],
                "dom_snapshot": '<div class="search-results"><div class="result" data-rank="1"><h3>Cooking Basics</h3><span class="score">0.42</span></div><div class="result" data-rank="2"><h3>Python Tutorial</h3><span class="score">0.38</span></div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["relevance", "scoring", "boost", "weight", "ranking", "regression"],
            },
            {
                "test_id": "test_facet_count_accuracy",
                "name": "Facet filter counts match the number of actual results in each category",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Facet 'Electronics' shows count 45 but filtered results returned 38 items\n"
                    "  Index not rebuilt after schema change — stale facet counts\n"
                    "  at test/e2e/facets.spec.js:52"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(expected)\n"
                    "    at Object.<anonymous> (test/e2e/facets.spec.js:52:36)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)"
                ),
                "console_logs": [
                    "[INFO] Loading facets for query: '*' with category aggregation",
                    "[WARN] Facet count for 'Electronics': 45 (from cached index), actual filtered count: 38",
                    "[ERROR] Index was last rebuilt on 2026-03-28, schema changed on 2026-03-30 — 7 products recategorized",
                    "[WARN] Stale index causing facet count mismatch — run reindex to fix",
                ],
                "dom_snapshot": '<div class="facets"><div class="facet"><label>Electronics</label><span class="count">45</span></div><div class="facet"><label>Books</label><span class="count">120</span></div></div>',
                "history": [True, True, True, True, True, True, True, True, False, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["facet", "count", "mismatch", "index", "schema", "rebuild"],
            },
            {
                "test_id": "test_autocomplete_suggestions",
                "name": "Autocomplete dropdown shows relevant suggestions as user types",
                "category": "flaky_test",
                "error_output": (
                    "TimeoutError: Expected autocomplete dropdown to show 5 suggestions within 2000ms but found 0\n"
                    "  Debounce delay plus API latency exceeded assertion timeout\n"
                    "  at test/e2e/autocomplete.spec.js:28"
                ),
                "stack_trace": (
                    "TimeoutError: waiting for selector '.suggestion-item' count to be 5\n"
                    "    at waitForFunction (node_modules/playwright/lib/frames.js:210:15)\n"
                    "    at test/e2e/autocomplete.spec.js:28:18"
                ),
                "console_logs": [
                    "[INFO] User typed: 'pyth' in search box",
                    "[INFO] Debounce timer: waiting 300ms before sending autocomplete request",
                    "[WARN] Autocomplete API response took 1850ms on CI (normally ~200ms locally)",
                    "[INFO] Suggestions rendered at 2150ms — 150ms after assertion timeout",
                ],
                "dom_snapshot": '<div class="search-box"><input type="text" value="pyth" /><div class="autocomplete-dropdown"><div class="loading">Loading...</div></div></div>',
                "history": [True, True, False, True, False, True, True, False, True, True],
                "recommendation": "rerun",
                "evidence_keywords": ["debounce", "timing", "autocomplete", "inconsistent", "race condition"],
            },
            {
                "test_id": "test_elasticsearch_bulk_index",
                "name": "Bulk indexing operation completes and all documents are searchable",
                "category": "environment_issue",
                "error_output": (
                    "Error: Elasticsearch bulk index request failed\n"
                    "  ClusterBlockException: index [articles] blocked by: [FORBIDDEN/12/index read-only / allow delete (api)]\n"
                    "  at test/e2e/bulk-index.spec.js:19"
                ),
                "stack_trace": (
                    "ClusterBlockException: [FORBIDDEN/12/index read-only]\n"
                    "    at ElasticsearchClient.bulk (src/search/esClient.js:45:11)\n"
                    "    at test/e2e/bulk-index.spec.js:19:24"
                ),
                "console_logs": [
                    "[INFO] Starting bulk index of 500 documents to index 'articles'",
                    "[ERROR] Elasticsearch cluster responded with 403: index read-only (disk full)",
                    "[ERROR] Staging ES cluster disk usage: 94.7% — threshold is 90%, cluster auto-locked to read-only",
                    "[WARN] Ops alert #SRE-1220: Elasticsearch staging cluster disk full — needs cleanup",
                ],
                "dom_snapshot": '<div class="index-status"><span class="cluster-health red">RED</span><span class="disk-usage">94.7%</span><span class="index-state">READ-ONLY</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["Elasticsearch", "disk", "full", "staging", "cluster", "infrastructure"],
            },
            {
                "test_id": "test_search_pagination_v1",
                "name": "Search pagination returns correct page of results using offset/limit",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected response to have 'offset' and 'limit' fields but got 'cursor' and 'pageSize'\n"
                    "  v1 pagination API was replaced by cursor-based pagination in v2\n"
                    "  at test/e2e/pagination-v1.spec.js:33"
                ),
                "stack_trace": (
                    "Error: expect(received).toHaveProperty('offset')\n"
                    "    at Object.<anonymous> (test/e2e/pagination-v1.spec.js:33:26)"
                ),
                "console_logs": [
                    "[INFO] GET /api/v1/search?q=test&offset=20&limit=10 — endpoint deprecated",
                    "[WARN] v1 pagination API removed in favor of cursor-based v2 (PR #912)",
                    "[INFO] Redirected to /api/v2/search?q=test&cursor=abc123&pageSize=10",
                    "[INFO] Response contains: {cursor: 'abc123', pageSize: 10, results: [...]} — no offset/limit fields",
                ],
                "dom_snapshot": '<div class="pagination"><button class="load-more" data-cursor="abc123">Load More</button></div>',
                "history": [False, False, False, False, False, False, False, False, False, False],
                "recommendation": "update_test",
                "evidence_keywords": ["deprecated", "v1", "pagination", "cursor", "replaced", "stale"],
            },
        ],
        "recent_changes": [
            {
                "commit": "h4k7m2n",
                "author": "alex.dev",
                "message": "Adjust search relevance boosting weights for title and tags",
                "files_changed": ["src/search/relevance.js", "src/search/config.json"],
                "diff": (
                    "--- a/src/search/config.json\n"
                    "+++ b/src/search/config.json\n"
                    "@@ -3,5 +3,5 @@\n"
                    ' "boostWeights": {\n'
                    '-    "title": 2.0,\n'
                    '-    "body": 1.0,\n'
                    '-    "tags": 1.0\n'
                    '+    "title": 5.0,\n'
                    '+    "body": 1.0,\n'
                    '+    "tags": 3.0\n'
                    " }\n"
                ),
            },
            {
                "commit": "p5q8r1s",
                "author": "dana.dev",
                "message": "Recategorize 7 products from Electronics to Gadgets in catalog schema",
                "files_changed": ["src/catalog/schema.js", "src/db/migrations/0055_recategorize_products.sql"],
                "diff": (
                    "--- a/src/db/migrations/0055_recategorize_products.sql\n"
                    "+++ b/src/db/migrations/0055_recategorize_products.sql\n"
                    "@@ -0,0 +1,3 @@\n"
                    "+UPDATE products SET category = 'Gadgets' WHERE id IN (101,102,103,104,105,106,107);\n"
                    "+-- NOTE: Elasticsearch index must be rebuilt after this migration\n"
                    "+-- TODO: add reindex step to CI pipeline\n"
                ),
            },
            {
                "commit": "t6u9v3w",
                "author": "alex.dev",
                "message": "Replace v1 offset/limit pagination with cursor-based pagination (PR #912)",
                "files_changed": ["src/api/search.js", "src/search/paginator.js"],
                "diff": (
                    "--- a/src/api/search.js\n"
                    "+++ b/src/api/search.js\n"
                    "@@ -12,8 +12,8 @@\n"
                    " router.get('/api/v2/search', async (req, res) => {\n"
                    "-  const { q, offset = 0, limit = 10 } = req.query;\n"
                    "-  const results = await search(q, { offset, limit });\n"
                    "-  res.json({ results, offset, limit, total: results.total });\n"
                    "+  const { q, cursor, pageSize = 10 } = req.query;\n"
                    "+  const results = await search(q, { cursor, pageSize });\n"
                    "+  res.json({ results: results.items, cursor: results.nextCursor, pageSize });\n"
                    " });\n"
                ),
            },
        ],
        "source_files": {
            "src/search/relevance.js": (
                "const config = require('./config.json');\n\n"
                "function scoreDocument(query, doc) {\n"
                "  const titleScore = matchScore(query, doc.title) * config.boostWeights.title;\n"
                "  const bodyScore = matchScore(query, doc.body) * config.boostWeights.body;\n"
                "  const tagScore = matchScore(query, doc.tags.join(' ')) * config.boostWeights.tags;\n"
                "  return titleScore + bodyScore + tagScore;\n"
                "}\n\n"
                "function matchScore(query, text) {\n"
                "  // TF-IDF based scoring\n"
                "  const terms = query.toLowerCase().split(' ');\n"
                "  return terms.reduce((score, term) => {\n"
                "    return score + (text.toLowerCase().includes(term) ? 1 : 0);\n"
                "  }, 0) / terms.length;\n"
                "}\n\n"
                "module.exports = { scoreDocument };\n"
            ),
            "src/search/esClient.js": (
                "const { Client } = require('@elastic/elasticsearch');\n\n"
                "const client = new Client({ node: process.env.ES_URL || 'http://localhost:9200' });\n\n"
                "async function bulk(index, documents) {\n"
                "  const body = documents.flatMap(doc => [\n"
                "    { index: { _index: index, _id: doc.id } },\n"
                "    doc,\n"
                "  ]);\n"
                "  const result = await client.bulk({ body });\n"
                "  if (result.errors) throw new Error('Bulk index failed');\n"
                "  return result;\n"
                "}\n\n"
                "module.exports = { bulk, client };\n"
            ),
            "src/api/search.js": (
                "const express = require('express');\n"
                "const { search } = require('../search/engine');\n"
                "const router = express.Router();\n\n"
                "router.get('/api/v2/search', async (req, res) => {\n"
                "  const { q, cursor, pageSize = 10 } = req.query;\n"
                "  const results = await search(q, { cursor, pageSize });\n"
                "  res.json({ results: results.items, cursor: results.nextCursor, pageSize });\n"
                "});\n\n"
                "module.exports = router;\n"
            ),
            "test/e2e/search-relevance.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('search results ranked by relevance', async ({ page }) => {\n"
                "  await page.goto('/search?q=python+programming');\n"
                "  await page.waitForSelector('.result');\n"
                "  const firstResult = await page.textContent('.result[data-rank=\"1\"] h3');\n"
                "  expect(firstResult).toBe('Python Tutorial'); // line 39\n"
                "});\n"
            ),
        },
    },

    # ── Scenario 10: Authentication Flow ──
    {
        "id": "authentication_flow",
        "app_description": "Authentication flow — OAuth, MFA, session management, password reset, and account security E2E tests.",
        "test_summary": {"total": 26, "passed": 21, "failed": 5, "skipped": 0},
        "failed_tests": [
            {
                "test_id": "test_mfa_totp_validation",
                "name": "MFA TOTP code validation accepts valid 6-digit codes within time window",
                "category": "genuine_bug",
                "error_output": (
                    "AssertionError: Expected TOTP validation to return true but got false\n"
                    "  Valid TOTP code '482951' rejected — time window narrowed from +-1 to +-0 steps\n"
                    "  at test/e2e/mfa-totp.spec.js:44"
                ),
                "stack_trace": (
                    "Error: expect(received).toBe(true)\n"
                    "    at Object.<anonymous> (test/e2e/mfa-totp.spec.js:44:38)\n"
                    "    at Object.asyncJestTest (node_modules/jest/build/jasmine.js:102:37)"
                ),
                "console_logs": [
                    "[INFO] TOTP validation for user_id=u-2001, code=482951",
                    "[INFO] Server time: 2026-04-11T10:30:45Z, TOTP step: 54348681",
                    "[WARN] Code '482951' valid for step 54348680 (previous step) — rejected because window=0 (was window=1)",
                    "[ERROR] TOTP validation failed: code is for adjacent time step but strict mode rejects it after security hardening PR #1042",
                ],
                "dom_snapshot": '<div class="mfa-form"><input type="text" class="totp-input" value="482951" /><span class="error-message">Invalid code. Please try again.</span></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["TOTP", "time window", "validation", "security hardening", "too strict", "regression"],
            },
            {
                "test_id": "test_password_reset_email",
                "name": "Password reset sends email with valid reset token link",
                "category": "genuine_bug",
                "error_output": (
                    "Error: Email send failed — SMTP rejected message: 550 5.1.1 Sender address rejected\n"
                    "  From address 'noreply@old-domain.com' is no longer valid after domain migration\n"
                    "  at test/e2e/password-reset.spec.js:37"
                ),
                "stack_trace": (
                    "SMTPError: 550 5.1.1 Sender address rejected: noreply@old-domain.com\n"
                    "    at SMTPTransport.send (src/email/transport.js:42:11)\n"
                    "    at sendResetEmail (src/auth/passwordReset.js:28:5)\n"
                    "    at test/e2e/password-reset.spec.js:37:22"
                ),
                "console_logs": [
                    "[INFO] Password reset requested for email: alice@example.com",
                    "[INFO] Reset token generated: tok_abc123def456 (expires in 1h)",
                    "[ERROR] SMTP send failed: 550 Sender 'noreply@old-domain.com' rejected — domain migrated to 'noreply@newapp.io'",
                    "[WARN] Email config still references old domain — update EMAIL_FROM in config",
                ],
                "dom_snapshot": '<div class="reset-form"><p>A reset link has been sent to your email.</p><div class="error-toast" style="display:block">Failed to send email. Contact support.</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "fix_code",
                "evidence_keywords": ["password reset", "email", "from address", "sending", "configuration", "regression"],
            },
            {
                "test_id": "test_oauth_callback_redirect",
                "name": "OAuth callback redirects user to dashboard after successful authentication",
                "category": "flaky_test",
                "error_output": (
                    "TimeoutError: Waiting for navigation to '/dashboard' exceeded 10000ms\n"
                    "  OAuth provider callback took 9500ms (within timeout) but redirect was slow\n"
                    "  at test/e2e/oauth-callback.spec.js:55"
                ),
                "stack_trace": (
                    "TimeoutError: page.waitForNavigation: Timeout 10000ms exceeded\n"
                    "    at Page.waitForNavigation (node_modules/playwright/lib/page.js:312:15)\n"
                    "    at test/e2e/oauth-callback.spec.js:55:20"
                ),
                "console_logs": [
                    "[INFO] Initiating OAuth flow with provider: Google",
                    "[INFO] Redirected to OAuth provider authorization page",
                    "[WARN] OAuth provider response time: 9500ms (typical: 1000-3000ms, CI occasionally slower)",
                    "[INFO] Callback received at /auth/callback?code=auth_xyz — processing token exchange",
                ],
                "dom_snapshot": '<div class="auth-loading"><div class="spinner">Completing sign-in...</div><p>Redirecting to dashboard...</p></div>',
                "history": [True, False, True, True, False, True, True, True, False, True],
                "recommendation": "rerun",
                "evidence_keywords": ["OAuth", "callback", "timeout", "provider", "intermittent", "slow response"],
            },
            {
                "test_id": "test_ldap_login",
                "name": "LDAP login authenticates user against corporate directory",
                "category": "environment_issue",
                "error_output": (
                    "Error: LDAP bind failed — TLS handshake error\n"
                    "  DEPTH_ZERO_SELF_SIGNED_CERT: certificate has expired\n"
                    "  at test/e2e/ldap-login.spec.js:22"
                ),
                "stack_trace": (
                    "Error: DEPTH_ZERO_SELF_SIGNED_CERT\n"
                    "    at TLSSocket.onConnectSecure (node:tls:1530:34)\n"
                    "    at LDAPClient.bind (src/auth/ldapClient.js:31:9)\n"
                    "    at test/e2e/ldap-login.spec.js:22:18"
                ),
                "console_logs": [
                    "[INFO] LDAP bind attempt to ldaps://ldap.staging.corp.internal:636",
                    "[ERROR] TLS handshake failed: certificate expired on 2026-04-08 (3 days ago)",
                    "[ERROR] Staging LDAP server certificate not renewed — ops ticket #SRE-1305 pending",
                    "[WARN] LDAP authentication unavailable until certificate is rotated",
                ],
                "dom_snapshot": '<div class="login-form"><input type="text" placeholder="Corporate ID" /><input type="password" /><div class="error-banner">Corporate login unavailable. Certificate error.</div></div>',
                "history": [True, True, True, True, True, True, True, True, True, False],
                "recommendation": "check_infra",
                "evidence_keywords": ["LDAP", "certificate", "expired", "staging", "TLS", "infrastructure"],
            },
            {
                "test_id": "test_session_cookie_format",
                "name": "Session cookie is set with correct format and security attributes",
                "category": "stale_test",
                "error_output": (
                    "AssertionError: Expected cookie 'session' to have format 'sid=<value>' but got 'session=<jwt>; HttpOnly; SameSite=Strict'\n"
                    "  Cookie format changed during httpOnly+sameSite security migration\n"
                    "  at test/e2e/session-cookie.spec.js:29"
                ),
                "stack_trace": (
                    "Error: expect(received).toMatch(/^sid=/)\n"
                    "    at Object.<anonymous> (test/e2e/session-cookie.spec.js:29:30)"
                ),
                "console_logs": [
                    "[INFO] Session created for user_id=u-1001 after successful login",
                    "[INFO] Cookie set: session=eyJhbGciOi...; HttpOnly; SameSite=Strict; Secure; Path=/",
                    "[INFO] Cookie format migrated from 'sid=<uuid>' to 'session=<jwt>' with HttpOnly+SameSite (JIRA-6100)",
                ],
                "dom_snapshot": '<div class="session-debug"><pre>Cookie: session=eyJhbGciOiJIUzI1NiJ9...; HttpOnly; SameSite=Strict; Secure</pre></div>',
                "history": [False, False, False, False, False, True, True, True, True, True],
                "recommendation": "update_test",
                "evidence_keywords": ["cookie", "format", "httpOnly", "sameSite", "migration", "stale"],
            },
        ],
        "recent_changes": [
            {
                "commit": "k2m5n8p",
                "author": "security.bot",
                "message": "Harden TOTP validation: reduce time window from +-1 to +-0 steps (PR #1042)",
                "files_changed": ["src/auth/totp.js", "src/config/security.json"],
                "diff": (
                    "--- a/src/auth/totp.js\n"
                    "+++ b/src/auth/totp.js\n"
                    "@@ -10,5 +10,5 @@\n"
                    " function validateTOTP(secret, code) {\n"
                    "-  return speakeasy.totp.verify({ secret, encoding: 'base32', token: code, window: 1 });\n"
                    "+  return speakeasy.totp.verify({ secret, encoding: 'base32', token: code, window: 0 });\n"
                    "+  // Hardened: window=0 means only current 30s step accepted (was +-1 = 90s)\n"
                    " }\n"
                ),
            },
            {
                "commit": "q3r6s9t",
                "author": "devops.jen",
                "message": "Migrate email sender domain from old-domain.com to newapp.io",
                "files_changed": ["src/config/email.json", "src/email/transport.js"],
                "diff": (
                    "--- a/src/config/email.json\n"
                    "+++ b/src/config/email.json\n"
                    "@@ -2,3 +2,3 @@\n"
                    '-  "from": "noreply@old-domain.com",\n'
                    '+  "from": "noreply@old-domain.com",  // BUG: should be noreply@newapp.io\n'
                    '   "smtp_host": "smtp.newapp.io",\n'
                    '   "smtp_port": 587\n'
                ),
            },
            {
                "commit": "v1w4x7y",
                "author": "security.bot",
                "message": "Migrate session cookies to JWT format with HttpOnly and SameSite (JIRA-6100)",
                "files_changed": ["src/auth/session.js", "src/middleware/cookies.js"],
                "diff": (
                    "--- a/src/auth/session.js\n"
                    "+++ b/src/auth/session.js\n"
                    "@@ -8,6 +8,8 @@\n"
                    " function createSession(userId) {\n"
                    "-  const sid = uuid();\n"
                    "-  res.cookie('sid', sid);\n"
                    "+  const token = jwt.sign({ userId }, SECRET, { expiresIn: '24h' });\n"
                    "+  res.cookie('session', token, {\n"
                    "+    httpOnly: true,\n"
                    "+    sameSite: 'Strict',\n"
                    "+    secure: true,\n"
                    "+  });\n"
                    " }\n"
                ),
            },
        ],
        "source_files": {
            "src/auth/totp.js": (
                "const speakeasy = require('speakeasy');\n\n"
                "function validateTOTP(secret, code) {\n"
                "  return speakeasy.totp.verify({\n"
                "    secret,\n"
                "    encoding: 'base32',\n"
                "    token: code,\n"
                "    window: 0, // Hardened: only current 30s step (was window: 1)\n"
                "  });\n"
                "}\n\n"
                "module.exports = { validateTOTP };\n"
            ),
            "src/auth/passwordReset.js": (
                "const emailConfig = require('../config/email.json');\n"
                "const { sendEmail } = require('../email/transport');\n"
                "const crypto = require('crypto');\n\n"
                "async function sendResetEmail(userEmail) {\n"
                "  const token = crypto.randomBytes(32).toString('hex');\n"
                "  const resetLink = `https://app.newapp.io/reset?token=${token}`;\n"
                "  await sendEmail({\n"
                "    from: emailConfig.from, // BUG: still 'noreply@old-domain.com'\n"
                "    to: userEmail,\n"
                "    subject: 'Password Reset',\n"
                "    body: `Click here to reset: ${resetLink}`,\n"
                "  });\n"
                "  return token;\n"
                "}\n\n"
                "module.exports = { sendResetEmail };\n"
            ),
            "src/auth/session.js": (
                "const jwt = require('jsonwebtoken');\n"
                "const SECRET = process.env.SESSION_SECRET;\n\n"
                "function createSession(userId, res) {\n"
                "  const token = jwt.sign({ userId }, SECRET, { expiresIn: '24h' });\n"
                "  res.cookie('session', token, {\n"
                "    httpOnly: true,\n"
                "    sameSite: 'Strict',\n"
                "    secure: true,\n"
                "  });\n"
                "}\n\n"
                "module.exports = { createSession };\n"
            ),
            "test/e2e/mfa-totp.spec.js": (
                "const { test, expect } = require('@playwright/test');\n\n"
                "test('TOTP validation accepts valid code', async ({ page }) => {\n"
                "  await page.goto('/login/mfa');\n"
                "  await page.fill('.totp-input', '482951');\n"
                "  await page.click('#verify-btn');\n"
                "  const result = await page.textContent('.mfa-status');\n"
                "  expect(result).not.toContain('Invalid'); // line 44\n"
                "});\n"
            ),
        },
    },
]


# ── Closed-vocabulary overlay ──
# Each failed test gets a structured `evidence_tags` list picked from
# rewards.EVIDENCE_TAGS based on its category. The grader F1-scores the tag
# set instead of grading prose evidence — that kills keyword stuffing.

_CATEGORY_DEFAULT_TAGS: dict[str, list[str]] = {
    "genuine_bug": ["recent_code_change", "regression"],
    "flaky_test": ["intermittent", "timing_dependent", "passes_on_rerun"],
    "environment_issue": ["external_service_down", "infrastructure_failure"],
    "stale_test": ["outdated_assertion", "intentional_change"],
}

_TEST_SCENARIO_IDS: set[str] = {"project_tracker", "search_engine", "authentication_flow"}

for _s in SCENARIOS:
    _s["split"] = "test" if _s["id"] in _TEST_SCENARIO_IDS else "train"
    for _t in _s.get("failed_tests", []):
        _t["evidence_tags"] = list(_CATEGORY_DEFAULT_TAGS[_t["category"]])
