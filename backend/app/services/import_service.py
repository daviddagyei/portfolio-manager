"""
Import service for handling portfolio and asset data imports.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
import csv
import io
import structlog

from app.models import Portfolio as PortfolioModel, Asset as AssetModel, PortfolioHolding
from app.schemas import PortfolioCreate, Portfolio
from app.services.portfolio_service import PortfolioService
from app.services.asset_service import AssetService

logger = structlog.get_logger()


class ImportService:
    """Service for importing portfolio and asset data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.portfolio_service = PortfolioService(db)
        self.asset_service = AssetService(db)
    
    async def import_portfolio_from_csv(
        self, 
        csv_data: str, 
        portfolio_data: Dict[str, Any]
    ) -> Portfolio:
        """
        Import portfolio holdings from CSV data.
        
        Args:
            csv_data: CSV string containing holding data
            portfolio_data: Portfolio information (name, type, etc.)
            
        Returns:
            Created portfolio with holdings
        """
        try:
            # Parse CSV data
            holdings_data = self._parse_csv_data(csv_data)
            
            # Validate data
            validation_errors = self._validate_holdings_data(holdings_data)
            if validation_errors:
                raise ValueError(f"Data validation failed: {'; '.join(validation_errors)}")
            
            # Create portfolio
            portfolio_create = PortfolioCreate(
                name=portfolio_data['name'],
                description=portfolio_data.get('description', ''),
                portfolioType=portfolio_data.get('portfolioType', 'investment'),
                initialValue=Decimal('0')  # Will be calculated from holdings
            )
            
            portfolio = await self.portfolio_service.create_portfolio(portfolio_create)
            
            # Process holdings
            total_initial_value = Decimal('0')
            created_holdings = []
            
            for holding_data in holdings_data:
                # Create or get asset
                asset = await self._create_or_get_asset(holding_data)
                
                # Create holding
                holding = PortfolioHolding(
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    quantity=Decimal(str(holding_data['quantity'])),
                    average_cost=Decimal(str(holding_data['average_cost'])),
                    current_price=Decimal(str(holding_data.get('current_price', holding_data['average_cost']))),
                    market_value=Decimal(str(holding_data['quantity'])) * Decimal(str(holding_data.get('current_price', holding_data['average_cost']))),
                    unrealized_gain_loss=Decimal('0'),  # Will be calculated
                    unrealized_gain_loss_percentage=Decimal('0')  # Will be calculated
                )
                
                self.db.add(holding)
                created_holdings.append(holding)
                
                # Add to initial value
                cost_basis = holding.quantity * holding.average_cost
                total_initial_value += cost_basis
            
            # Update portfolio initial value
            portfolio_model = self.db.query(PortfolioModel).filter(
                PortfolioModel.id == portfolio.id
            ).first()
            
            if portfolio_model:
                portfolio_model.initial_value = total_initial_value
                portfolio_model.current_value = sum(h.market_value for h in created_holdings)
                portfolio_model.total_return = portfolio_model.current_value - portfolio_model.initial_value
                
                if portfolio_model.initial_value > 0:
                    portfolio_model.total_return_percentage = (
                        portfolio_model.total_return / portfolio_model.initial_value
                    ) * 100
                else:
                    portfolio_model.total_return_percentage = Decimal('0')
            
            self.db.commit()
            
            # Refresh portfolio data
            updated_portfolio = await self.portfolio_service.get_portfolio(portfolio.id)
            
            logger.info(
                "Portfolio imported successfully",
                portfolio_id=portfolio.id,
                holdings_count=len(created_holdings),
                initial_value=float(total_initial_value)
            )
            
            return updated_portfolio
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error importing portfolio", error=str(e))
            raise
    
    def _parse_csv_data(self, csv_data: str) -> List[Dict[str, Any]]:
        """Parse CSV data into list of dictionaries."""
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            holdings = []
            
            for row in reader:
                # Clean and normalize field names
                cleaned_row = {}
                for key, value in row.items():
                    clean_key = key.strip().lower().replace(' ', '_')
                    cleaned_row[clean_key] = value.strip() if value else ''
                
                holdings.append(cleaned_row)
            
            return holdings
            
        except Exception as e:
            logger.error("Error parsing CSV data", error=str(e))
            raise ValueError(f"Failed to parse CSV data: {str(e)}")
    
    def _validate_holdings_data(self, holdings_data: List[Dict[str, Any]]) -> List[str]:
        """Validate holdings data and return list of errors."""
        errors = []
        required_fields = ['symbol', 'quantity', 'price']
        
        for i, holding in enumerate(holdings_data):
            row_num = i + 1
            
            # Check required fields
            for field in required_fields:
                if field not in holding or not holding[field]:
                    errors.append(f"Row {row_num}: Missing {field}")
            
            # Validate numeric fields
            if 'quantity' in holding and holding['quantity']:
                try:
                    quantity = float(holding['quantity'])
                    if quantity <= 0:
                        errors.append(f"Row {row_num}: Quantity must be positive")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid quantity value")
            
            if 'price' in holding and holding['price']:
                try:
                    price = float(holding['price'])
                    if price <= 0:
                        errors.append(f"Row {row_num}: Price must be positive")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid price value")
            
            # Validate symbol
            if 'symbol' in holding and holding['symbol']:
                symbol = holding['symbol'].strip().upper()
                if len(symbol) < 1 or len(symbol) > 10:
                    errors.append(f"Row {row_num}: Invalid symbol length")
                if not symbol.isalnum():
                    errors.append(f"Row {row_num}: Symbol must be alphanumeric")
        
        return errors
    
    async def _create_or_get_asset(self, holding_data: Dict[str, Any]) -> AssetModel:
        """Create or retrieve asset based on holding data."""
        symbol = holding_data['symbol'].strip().upper()
        
        # Try to get existing asset
        asset = await self.asset_service.get_asset_by_symbol(symbol)
        
        if not asset:
            # Create new asset
            asset_data = {
                'symbol': symbol,
                'name': holding_data.get('name', symbol),
                'asset_type': holding_data.get('asset_type', 'stock').lower(),
                'sector': holding_data.get('sector'),
                'market': holding_data.get('market', 'US'),
                'currency': holding_data.get('currency', 'USD'),
                'is_active': True
            }
            
            asset = await self.asset_service.create_asset(asset_data)
        
        return asset
    
    async def export_portfolio_to_csv(self, portfolio_id: int) -> str:
        """Export portfolio holdings to CSV format."""
        try:
            # Get portfolio holdings
            holdings = await self.portfolio_service.get_portfolio_holdings(portfolio_id)
            
            if not holdings:
                return "symbol,quantity,average_cost,current_price,market_value,asset_type,sector\n"
            
            # Create CSV content
            output = io.StringIO()
            fieldnames = [
                'symbol', 'name', 'quantity', 'average_cost', 'current_price', 
                'market_value', 'unrealized_gain_loss', 'unrealized_gain_loss_percentage',
                'asset_type', 'sector'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for holding in holdings:
                writer.writerow({
                    'symbol': holding['asset_symbol'],
                    'name': holding['asset_name'],
                    'quantity': holding['quantity'],
                    'average_cost': holding['average_cost'],
                    'current_price': holding['current_price'],
                    'market_value': holding['market_value'],
                    'unrealized_gain_loss': holding['unrealized_gain_loss'],
                    'unrealized_gain_loss_percentage': holding['unrealized_gain_loss_percentage'],
                    'asset_type': holding['asset_type'],
                    'sector': holding['sector']
                })
            
            return output.getvalue()
            
        except Exception as e:
            logger.error("Error exporting portfolio to CSV", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def import_transactions_from_csv(
        self, 
        csv_data: str, 
        portfolio_id: int
    ) -> List[Dict[str, Any]]:
        """Import transaction data from CSV."""
        try:
            # Parse CSV data
            transactions_data = self._parse_csv_data(csv_data)
            
            # Validate transaction data
            validation_errors = self._validate_transaction_data(transactions_data)
            if validation_errors:
                raise ValueError(f"Transaction data validation failed: {'; '.join(validation_errors)}")
            
            # Process transactions (placeholder - would need transaction service)
            processed_transactions = []
            
            for transaction_data in transactions_data:
                # This would typically create actual transactions
                # For now, just return the processed data
                processed_transactions.append({
                    'symbol': transaction_data['symbol'],
                    'type': transaction_data['type'],
                    'quantity': transaction_data['quantity'],
                    'price': transaction_data['price'],
                    'date': transaction_data['date'],
                    'fees': transaction_data.get('fees', 0)
                })
            
            logger.info(
                "Transactions imported successfully",
                portfolio_id=portfolio_id,
                transaction_count=len(processed_transactions)
            )
            
            return processed_transactions
            
        except Exception as e:
            logger.error("Error importing transactions", portfolio_id=portfolio_id, error=str(e))
            raise
    
    def _validate_transaction_data(self, transactions_data: List[Dict[str, Any]]) -> List[str]:
        """Validate transaction data and return list of errors."""
        errors = []
        required_fields = ['symbol', 'type', 'quantity', 'price', 'date']
        valid_types = ['buy', 'sell', 'dividend', 'split']
        
        for i, transaction in enumerate(transactions_data):
            row_num = i + 1
            
            # Check required fields
            for field in required_fields:
                if field not in transaction or not transaction[field]:
                    errors.append(f"Row {row_num}: Missing {field}")
            
            # Validate transaction type
            if 'type' in transaction and transaction['type']:
                if transaction['type'].lower() not in valid_types:
                    errors.append(f"Row {row_num}: Invalid transaction type")
            
            # Validate numeric fields
            for field in ['quantity', 'price']:
                if field in transaction and transaction[field]:
                    try:
                        value = float(transaction[field])
                        if value <= 0:
                            errors.append(f"Row {row_num}: {field} must be positive")
                    except ValueError:
                        errors.append(f"Row {row_num}: Invalid {field} value")
            
            # Validate date
            if 'date' in transaction and transaction['date']:
                try:
                    datetime.strptime(transaction['date'], '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid date format (use YYYY-MM-DD)")
        
        return errors
