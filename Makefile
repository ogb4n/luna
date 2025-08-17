# Makefile for Luna Voice Bot

.PHONY: help build run stop logs clean dev-build dev-run dev-stop

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build the production Docker image"
	@echo "  run       - Run the bot in production mode"
	@echo "  stop      - Stop the running bot"
	@echo "  logs      - Show bot logs"
	@echo "  clean     - Remove containers and images"
	@echo "  dev-build - Build development image"
	@echo "  dev-run   - Run bot in development mode"
	@echo "  dev-stop  - Stop development bot"

# Production commands
build:
	docker-compose build --no-cache

run:
	docker-compose up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f luna-bot

# Development commands
dev-build:
	docker-compose -f docker-compose.dev.yml build --no-cache

dev-run:
	docker-compose -f docker-compose.dev.yml up

dev-stop:
	docker-compose -f docker-compose.dev.yml down

# Cleanup
clean:
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# Health check
health:
	docker-compose exec luna-bot python -c "print('Bot is healthy!')"
