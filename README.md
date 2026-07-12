# WizX Calendar

High Impact Economic Calendar for Forex & Gold Traders.

## Features

- Generates a valid RFC 5545 ICS feed for high-impact economic events
- Publishes JSON data alongside the calendar feed
- Exposes lightweight REST endpoints for today, week, and next events
- Uses a provider abstraction so the data source can be replaced later
- Supports retrying provider requests with exponential backoff and structured logging
- Ready for GitHub Pages deployment and GitHub Actions automation

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Development

Run the API locally:

```bash
uvicorn src.api.main:app --reload
```

Generate the static outputs:

```bash
python -m src.api.main
```

## Provider configuration

The project now uses a live provider implementation by default. Configure an Alpha Vantage API key (or another permitted economic calendar provider) via the environment variables in [.env.example](.env.example). If no key is configured, the application falls back to a deterministic high-impact event feed so the calendar still renders locally and in CI.

## Deployment

The project is designed for GitHub Pages publication. The generated files are written to the output directory and can be served directly from the Pages site.

## GitHub Pages

The public calendar feed will be available at:

https://ashbelmax.github.io/wizx-calendar/high-impact.ics

## GitHub Actions

A workflow is included to fetch data, regenerate the calendar and JSON outputs, commit changes, and publish the site hourly.

## Apple Calendar

Subscribe to the ICS feed in Apple Calendar using the URL:

https://ashbelmax.github.io/wizx-calendar/high-impact.ics

## Google Calendar

Import the ICS feed into Google Calendar via the "Other calendars" import option.

## Outlook

Use the Outlook calendar import feature to add the ICS subscription.

## Roadmap

- Add a real economic-data provider with automatic retry and rate-limit handling
- Support richer event filtering and custom currencies
- Add more robust timezone and recurring-event support

## License

MIT
