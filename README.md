# Multi-Tenant SaaS Billing Platform

A multi-tenant backend for a subscription-based SaaS product, built with Django and Django REST Framework. Each company (tenant) has fully isolated users and data, with Stripe-powered billing and usage-based metering.

## Features

- **Multi-tenancy** — company-level data isolation enforced at the query level across all API endpoints
- **Stripe Checkout integration** — subscription billing with server-side payment verification and automatic plan activation on successful payment
- **Dual authentication** — JWT-secured REST API for programmatic access, plus session-based authentication for a Django-templated web dashboard
- **Usage-based metering** — tracks monthly consumption per tenant against plan-defined limits

## Tech Stack

Python · Django · Django REST Framework · Stripe API · JWT · Bootstrap 5

## Project Structure

- `accounts/` — user accounts and authentication
- `billing/` — Stripe integration, subscriptions, and usage metering
- `core/` — project settings and configuration
- `dashboard/` — session-based web dashboard (templates + views)
- `tenants/` — multi-tenant models, permissions, and API serializers

## Getting Started

1. Clone the repo and create a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Add a `.env` file with your Stripe keys and Django secret key
4. Run migrations: `python manage.py migrate`
5. Start the server: `python manage.py runserver`
