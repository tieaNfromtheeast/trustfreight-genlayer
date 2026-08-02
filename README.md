[Uploading README.md…](# TrustFreight

Intelligent Contract on GenLayer for cross-border logistics dispute resolution.

## Architecture
The system uses a multi-contract architecture:
- **TrustFreight Case**: The main contract handling dispute logic, receiving evidence (tracking URL, weather location, images), and calling the GenLayer AI Validator to determine Shipper/Carrier fault based on weather data (Open-Meteo) and actual tracking.
- **Escrow Treasury**: Escrow contract holding the deposit (GEN) and automatically disbursing funds based on the AI Validator's verdict (fault percentage).
- **Reputation Registry**: Stores the reputation score of Shipper and Carrier, automatically updating after each dispute.

## Live App
https://trustfreight-genlayer.vercel.app

## Deployed Contract
Contract Address (studionet): 0x53042d8b547f85f34716F07acFD3F62e7a91fdF9
Explorer: https://genlayer-explorer.vercel.app/address/0x53042d8b547f85f34716F07acFD3F62e7a91fdF9

## Local Development

Frontend is built with React + Vite + TailwindCSS and connects to GenLayer via `genlayer-js`.

1. Clone this repo.
2. Move into the `frontend/` directory.
3. Copy `.env.example` to `.env` and enter the contract address in `VITE_CONTRACT_ADDRESS`:
   ```bash
   cp .env.example .env
   ```
4. Install dependencies:
   ```bash
   npm install
   ```
5. Run the local dev server:
   ```bash
   npm run dev
   ```
)
