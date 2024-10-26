const logger = require("@src/utils/Logger").Logger.logger;

export function forceExit(reason: string, exitCode = 1): void {
    logger.error(reason)
    process.exit(exitCode)
}

// Custom Errors go here

export class ConfigError extends Error {
    constructor(message: any) {
        super();
        this.name = "ConfigError"
        this.message = message;
    }
}