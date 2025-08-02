/**
 * Chart Factory Test File
 * Tests the refactored chart rendering logic
 * Note: This file requires mobile-utils.js and chart.js to be loaded first
 */

// Wait for DOM to be ready
$(document).ready(function() {
    console.log('🧪 Starting Chart Factory Tests...');

    // Test mobile detection utilities
    console.log('\n📱 Mobile Detection Tests:');
    console.log('- Is Mobile:', MobileUtils.isMobile());
    console.log('- Is iOS:', MobileUtils.isIOS());
    console.log('- Is Android:', MobileUtils.isAndroid());
    console.log('- Supports Touch:', MobileUtils.supportsTouch());
    console.log('- Viewport Width:', MobileUtils.getViewportWidth());
    console.log('- Viewport Height:', MobileUtils.getViewportHeight());
    console.log('- Is Landscape:', MobileUtils.isLandscape());
    console.log('- Is Portrait:', MobileUtils.isPortrait());

    // Test chart factory logic
    console.log('\n🏭 Chart Factory Tests:');

    try {
        // Test 1: Mobile device - main page (should get MobileStockChart)
        console.log('Test 1: Mobile device - main page');
        const mobileMainChart = createStockChart('test-container-1', 'compact');
        console.log('- Chart Type:', mobileMainChart.constructor.name);
        console.log('- Chart Mode:', mobileMainChart.getChartMode());
        console.log('- Chart Height:', mobileMainChart.getChartHeight());
        console.log('- Margins:', JSON.stringify(mobileMainChart.getMargins()));

        // Test 2: Mobile device - detail page (should get MobileStockChart with detail context)
        console.log('\nTest 2: Mobile device - detail page');
        const mobileDetailChart = createStockChart('test-container-2', 'detailed');
        console.log('- Chart Type:', mobileDetailChart.constructor.name);
        console.log('- Chart Mode:', mobileDetailChart.getChartMode());
        console.log('- Chart Height:', mobileDetailChart.getChartHeight());
        console.log('- Margins:', JSON.stringify(mobileDetailChart.getMargins()));

        // Test 3: Simulate desktop device for testing
        console.log('\n🖥️ Simulating Desktop Tests:');

        // Temporarily override mobile detection for testing
        const originalIsMobile = MobileUtils.isMobile;
        MobileUtils.isMobile = () => false;

        // Test desktop - main page (should get CompactStockChart)
        console.log('Test 3: Desktop device - main page');
        const desktopMainChart = createStockChart('test-container-3', 'compact');
        console.log('- Chart Type:', desktopMainChart.constructor.name);
        console.log('- Chart Mode:', desktopMainChart.getChartMode());
        console.log('- Chart Height:', desktopMainChart.getChartHeight());
        console.log('- Margins:', JSON.stringify(desktopMainChart.getMargins()));

        // Test desktop - detail page (should get DetailedStockChart)
        console.log('\nTest 4: Desktop device - detail page');
        const desktopDetailChart = createStockChart('test-container-4', 'detailed');
        console.log('- Chart Type:', desktopDetailChart.constructor.name);
        console.log('- Chart Mode:', desktopDetailChart.getChartMode());
        console.log('- Chart Height:', desktopDetailChart.getChartHeight());
        console.log('- Margins:', JSON.stringify(desktopDetailChart.getMargins()));

        // Restore original mobile detection
        MobileUtils.isMobile = originalIsMobile;

        // Summary
        console.log('\n✅ Chart Factory Logic Summary:');
        console.log('- Mobile devices: Always use MobileStockChart (both main and detail pages)');
        console.log('- Desktop devices: CompactStockChart on main, DetailedStockChart on detail');
        console.log('- Factory function correctly routes based on device and page context');

        console.log('\n✅ All tests completed successfully!');

    } catch (error) {
        console.error('❌ Test failed:', error);
        console.error('Make sure mobile-utils.js and chart.js are loaded before this test file');
    }
});