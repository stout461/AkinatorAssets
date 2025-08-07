#!/usr/bin/env node

/**
 * Generate test status badge for README
 * This script can be run after tests to update the badge
 */

const fs = require('fs');
const path = require('path');

function generateBadge(status, testsRun, testsPassed) {
    const successRate = testsRun > 0 ? Math.round((testsPassed / testsRun) * 100) : 0;
    
    let color, label;
    if (status === 'success') {
        color = 'brightgreen';
        label = `${testsPassed}/${testsRun} passing`;
    } else {
        color = 'red';
        label = `${testsRun - testsPassed}/${testsRun} failing`;
    }
    
    const badgeUrl = `https://img.shields.io/badge/tests-${encodeURIComponent(label)}-${color}`;
    const badgeMarkdown = `![UI Tests](${badgeUrl})`;
    
    return {
        url: badgeUrl,
        markdown: badgeMarkdown,
        successRate
    };
}

// Example usage
if (require.main === module) {
    // This would typically read from test results
    const mockResults = {
        status: 'success',
        testsRun: 12,
        testsPassed: 12
    };
    
    const badge = generateBadge(mockResults.status, mockResults.testsRun, mockResults.testsPassed);
    console.log('Badge Markdown:', badge.markdown);
    console.log('Badge URL:', badge.url);
    console.log('Success Rate:', badge.successRate + '%');
}

module.exports = { generateBadge };