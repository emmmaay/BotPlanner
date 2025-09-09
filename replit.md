# Crypto Sniping Bot

## Overview

This is an automated cryptocurrency trading bot designed to monitor the Binance Smart Chain (BSC) for new token launches and execute trading strategies. The bot identifies newly listed tokens on PancakeSwap, performs comprehensive security analysis, and automatically executes buy/sell orders based on predefined criteria. It features real-time blockchain monitoring, portfolio management with automated profit-taking, and Telegram notifications for trade updates.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern
The bot follows a modular, event-driven architecture with asynchronous processing. Each component operates independently while communicating through callback functions and shared state management.

### Main Components

**Orchestrator (main_bot.py)**
- Central coordinator that initializes and manages all bot components
- Handles graceful shutdown and error recovery
- Implements signal handlers for clean termination

**Blockchain Monitor (blockchain_monitor.py)**
- Monitors BSC blockchain for new token launches and liquidity additions
- Tracks PancakeSwap factory events for new pair creation
- Uses Web3 to interact with blockchain RPC endpoints
- Maintains sets of monitored tokens and processed transactions to avoid duplicates

**Security Analyzer (security_analyzer.py)**
- Integrates with Go Plus Labs API for comprehensive token security analysis
- Performs honeypot detection, holder analysis, and liquidity verification
- Implements retry logic and rate limiting for API calls
- Uses configurable security thresholds for automated decision making

**Trading Engine (trading_engine.py)**
- Handles all PancakeSwap trading operations using Web3
- Manages wallet interactions and transaction signing
- Implements dynamic gas pricing and slippage protection
- Supports both buy and sell operations with configurable parameters

**Portfolio Manager (portfolio_manager.py)**
- Tracks all token positions and calculates profit/loss
- Implements automated profit-taking at configurable multipliers (5x, 10x)
- Persists portfolio state to JSON file for recovery after restarts
- Monitors token prices and executes partial sales based on profit targets

**Telegram Notifier (telegram_notifier.py)**
- Sends real-time notifications for token discoveries, trades, and portfolio updates
- Formats messages with HTML markup for better readability
- Implements error handling for Telegram API failures

### Configuration Management
Centralized configuration system using environment variables with fallback defaults. Supports blockchain endpoints, API keys, trading parameters, and profit-taking strategies.

### Error Handling and Resilience
- Comprehensive retry mechanisms for external API calls
- Graceful degradation when services are unavailable
- Signal handlers for clean shutdown
- Persistent portfolio state to survive restarts

### Logging System
Custom colored logging with different output levels and console formatting. Includes specialized logging for startup events, trades, and errors.

## External Dependencies

### Blockchain Infrastructure
- **Binance Smart Chain RPC**: Primary blockchain data source
- **BSCScan API**: Blockchain data verification and additional token information
- **Web3.py**: Ethereum/BSC blockchain interaction library

### Security Analysis
- **Go Plus Labs API**: Token security analysis, honeypot detection, and risk assessment
- Requires API key and secret for authenticated requests

### Trading Platform
- **PancakeSwap V2**: Decentralized exchange for token trading
- Router and Factory contracts for swap execution and pair monitoring
- WBNB contract for BNB wrapping/unwrapping operations

### Notifications
- **Telegram Bot API**: Real-time notifications and alerts
- Requires bot token and channel ID configuration

### Development Dependencies
- **aiohttp**: Async HTTP client for API calls
- **eth-account**: Ethereum account management and transaction signing
- **python-telegram-bot**: Telegram integration
- **colorama**: Terminal color formatting
- **retrying**: Retry logic for external service calls

### Data Persistence
- **JSON files**: Portfolio state and configuration persistence
- No external database required - uses local file storage