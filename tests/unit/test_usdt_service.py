from unittest.mock import patch

from src.services.usdt_service import USDTService


class TestUSDTService:
    """Unit tests for USDT service"""

    def test_get_payment_address(self):
        """Test getting payment address"""
        service = USDTService("0x1234567890abcdef")

        address = service.get_payment_address()
        assert address == "0x1234567890abcdef"

    def test_validate_transaction_placeholder(self):
        """Test transaction validation (currently placeholder)"""
        service = USDTService("0x1234567890abcdef")

        # Currently always returns True as placeholder
        result = service.validate_transaction("0xabcdef1234567890")
        assert result is True

    def test_get_payment_instructions(self):
        """Test payment instructions generation"""
        service = USDTService("0x1234567890abcdef")

        instructions = service.get_payment_instructions(10.50)

        expected_instructions = """
Para pagar com USDT Polygon:
1. Envie 10.5 USDT para: 0x1234567890abcdef
2. Use a rede Polygon
3. Envie o hash da transação para confirmação
"""

        assert instructions == expected_instructions

    def test_get_payment_instructions_different_amount(self):
        """Test payment instructions with different amount"""
        service = USDTService("0xabcdef1234567890")

        instructions = service.get_payment_instructions(25.0)

        assert "Envie 25.0 USDT para: 0xabcdef1234567890" in instructions
        assert "Use a rede Polygon" in instructions
        assert "Envie o hash da transação para confirmação" in instructions

    @patch("src.services.usdt_service.logger")
    def test_validate_transaction_logs(self, mock_logger):
        """Test that transaction validation logs the tx_hash"""
        service = USDTService("0x1234567890abcdef")

        tx_hash = "0xabcdef1234567890"
        result = service.validate_transaction(tx_hash)

        assert result is True
        mock_logger.info.assert_called_once_with(f"Validating USDT transaction: {tx_hash}")

    def test_service_initialization(self):
        """Test service initialization with wallet address"""
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        service = USDTService(wallet_address)

        assert service.wallet_address == wallet_address
        assert service.get_payment_address() == wallet_address
