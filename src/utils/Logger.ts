const winston = require("winston");
const { createLogger, format, transports } = winston;
const { combine, printf, colorize, prettyPrint } = format;
const DatadogWinston = require('datadog-winston');

import Config from "@src/core/Config";
import moment from "moment";

export abstract class Logger {
    private static payloadData: string;
    static payload = format.printf((info: any) => {
        if (info.message.constructor === Object) {
            info.message = JSON.stringify(info.message, null, 4);
        }
        Logger.payloadData = `${moment().format('YYYY-MM-DD THH:mm:ss.SSSZZ')} [${info.level}]: ${info.message}`;
        return Logger.payloadData;
    });

    static logger = createLogger({
        format: combine(
            format((info: any) => {
                info.level = info.level.toUpperCase()
                return info
            })(),
            printf((info: any) => {
                return Logger.payloadData;
            })
        ),
        transports: [
            new transports.Console({
                level: "debug",
                format: combine(
                    format((info: any) => {
                        info.level = info.level.toUpperCase();
                        return info;
                    })(),
                    colorize(),
                    Logger.payload
                )
            })
        ],
        exitOnError: true
    });

    static initDatadogTransport() {
        this.logger.add(
            new DatadogWinston({
                apiKey: Config.ddApiKey,
                hostname: Config.ddHostname,
                service: Config.ddService,
                ddsource: Config.ddSource,
                ddtags: Config.ddTags
            })
        )
    }
}