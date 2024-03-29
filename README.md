# CryptoGraph

## A tool for crypto-currency analysis.

CryptoGraph is a platform for data discovery and analysis of various cryptocurrencies and crypto exchange markets. The idea is to have a centralized dashboard that provides visualizations and machine learning for day trading of crypto's.

Most crypto exchange markets provide API endpoints for up/down IO. CryptoGraph aims to provide support for most major exchanges like Coinbase and Gemini. Even if your desired exchange is not officially supported, CryptoGraph provides an easy `Exchange` template that allows you to define the right endpoints and protocols. Once your `Exchange` class is fully defined, it will be immediately compatible with the `MarketData` class, and you'll be ready to start pulling data.
