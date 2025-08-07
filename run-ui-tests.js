#!/usr/bin/env node

/**
 * UI Test Automation Runner
 * Runs the complete test suite with proper setup and reporting
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ANSI color codes for console output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logHeader(message) {
    log('\n' + '='.repeat(60), 'cyan');
    log(`  ${message}`, 'bright');
    log('='.repeat(60), 'cyan');
}

function logStep(step, message) {
    log(`\n${step}. ${message}`, 'blue');
}

function logSuccess(message) {
    log(`✅ ${message}`, 'green');
}

function logError(message) {
    log(`❌ ${message}`, 'red');
}

function logWarning(message) {
    log(`⚠️  ${message}`, 'yellow');
}

function runCommand(command, description) {
    try {
        log(`\n🔄 ${description}...`, 'yellow');
        const output = execSync(command, { 
            stdio: 'inherit',
            encoding: 'utf8'
        });
        logSuccess(`${description} completed`);
        return true;
    } catch (error) {
        logError(`${description} failed`);
        logError(`Command: ${command}`);
        logError(`Error: ${error.message}`);
        return false;
    }
}

function checkPrerequisites() {
    logStep(1, 'Checking Prerequisites');
    
    // Check if Node.js is available
    try {
        execSync('node --version', { stdio: 'pipe' });
        logSuccess('Node.js is available');
    } catch (error) {
        logError('Node.js is not available');
        return false;
    }
    
    // Check if npm is available
    try {
        execSync('npm --version', { stdio: 'pipe' });
        logSuccess('npm is available');
    } catch (error) {
        logError('npm is not available');
        return false;
    }
    
    // Check if package.json exists
    if (fs.existsSync('package.json')) {
        logSuccess('package.json found');
    } else {
        logError('package.json not found');
        return false;
    }
    
    // Check if Playwright is installed
    try {
        execSync('npx playwright --version', { stdio: 'pipe' });
        logSuccess('Playwright is installed');
    } catch (error) {
        logWarning('Playwright not found - will attempt to install');
    }
    
    return true;
}

function installDependencies() {
    logStep(2, 'Installing Dependencies');
    
    if (!runCommand('npm install', 'Installing npm dependencies')) {
        return false;
    }
    
    if (!runCommand('npx playwright install chrome', 'Installing Chrome browser for Playwright')) {
        return false;
    }
    
    return true;
}

function runTestSuite() {
    logStep(3, 'Running UI Test Suite');
    
    const testSuites = [
        {
            name: 'Authentication Tests',
            command: 'npx playwright test tests/e2e/auth/auth-simple.spec.ts',
            description: 'Basic login/logout functionality'
        },
        {
            name: 'Dashboard Tests', 
            command: 'npx playwright test tests/e2e/dashboard/dashboard-functionality.spec.ts',
            description: 'Core dashboard features'
        },
        {
            name: 'Chart Interaction Tests',
            command: 'npx playwright test tests/e2e/chart/',
            description: 'Technical indicators, modes, and moving averages'
        }
    ];
    
    let allPassed = true;
    const results = [];
    
    for (const suite of testSuites) {
        log(`\n📊 Running ${suite.name}`, 'magenta');
        log(`   ${suite.description}`, 'reset');
        
        const success = runCommand(suite.command, `Executing ${suite.name}`);
        results.push({ name: suite.name, success });
        
        if (!success) {
            allPassed = false;
        }
    }
    
    // Summary
    logHeader('Test Results Summary');
    results.forEach(result => {
        if (result.success) {
            logSuccess(`${result.name}: PASSED`);
        } else {
            logError(`${result.name}: FAILED`);
        }
    });
    
    return allPassed;
}

function generateReport() {
    logStep(4, 'Generating Test Report');
    
    // Skip interactive report in CI environments
    if (process.env.CI || process.env.GITHUB_ACTIONS) {
        log('📊 Skipping interactive report in CI environment', 'yellow');
        logSuccess('Test report generated (available in test-results/)');
        return true;
    }
    
    if (runCommand('npx playwright show-report', 'Opening test report')) {
        logSuccess('Test report generated and opened');
        return true;
    }
    
    return false;
}

function main() {
    logHeader('UI Test Automation Suite');
    log('Stock Analysis Application - Automated Testing', 'bright');
    
    // Parse command line arguments
    const args = process.argv.slice(2);
    const isHeaded = args.includes('--headed');
    const isDebug = args.includes('--debug');
    
    if (isHeaded) {
        log('🖥️  Running in headed mode (visible browser)', 'yellow');
        process.env.PLAYWRIGHT_HEADED = 'true';
    }
    
    if (isDebug) {
        log('🐛 Running in debug mode', 'yellow');
        process.env.PLAYWRIGHT_DEBUG = 'true';
    }
    
    let success = true;
    
    // Step 1: Check prerequisites
    if (!checkPrerequisites()) {
        logError('Prerequisites check failed');
        process.exit(1);
    }
    
    // Step 2: Install dependencies
    if (!installDependencies()) {
        logError('Dependency installation failed');
        process.exit(1);
    }
    
    // Step 3: Run tests
    if (!runTestSuite()) {
        logError('Some tests failed');
        success = false;
    }
    
    // Step 4: Generate report (optional, don't fail if this doesn't work)
    if (!args.includes('--no-report')) {
        generateReport();
    }
    
    // Final summary
    logHeader('Execution Complete');
    if (success) {
        logSuccess('All tests passed successfully! 🎉');
        log('\nNext steps:', 'bright');
        log('• Review the test report for detailed results');
        log('• Check test-results/ directory for artifacts');
        log('• Run with --headed to see tests in action');
        process.exit(0);
    } else {
        logError('Some tests failed. Please review the output above.');
        log('\nTroubleshooting:', 'bright');
        log('• Check if the Flask application is running on port 8080');
        log('• Verify test credentials are configured correctly');
        log('• Run individual test files to isolate issues');
        process.exit(1);
    }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    logError(`Uncaught exception: ${error.message}`);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    logError(`Unhandled rejection at: ${promise}, reason: ${reason}`);
    process.exit(1);
});

// Run the main function
main();