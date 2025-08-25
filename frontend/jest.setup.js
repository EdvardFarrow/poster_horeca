import '@testing-library/jest-dom';


if (typeof TextEncoder === 'undefined') {
    global.TextEncoder = require('util').TextEncoder;
}