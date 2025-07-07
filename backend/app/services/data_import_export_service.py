import csv
import io
import pandas as pd
from typing import List, Dict, Optional, Union
from datetime import datetime
from decimal import Decimal
import structlog

from app.schemas import TransactionCreate, PortfolioCreate
from app.models import Asset as AssetModel, Portfolio as PortfolioModel


logger = structlog.get_logger()


class DataImportExportService:
    """Service for importing and exporting portfolio data."""
    
    def __init__(self, db=None):
        self.db = db
    
    async def import_transactions_from_csv(
        self, 
        file_content: bytes, 
        portfolio_id: int,
        user_id: int = 1
    ) -> Dict:
        """Import transactions from CSV file."""
        try:
            # Parse CSV content
            csv_string = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_string))
            
            transactions = []
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start from row 2 (header is row 1)
                try:
                    # Map CSV columns to transaction fields
                    transaction_data = await self._parse_transaction_row(row, portfolio_id)
                    transactions.append(transaction_data)
                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'error': str(e),
                        'data': row
                    })
            
            return {
                'success': True,
                'transactions': transactions,
                'total_parsed': len(transactions),
                'errors': errors,
                'error_count': len(errors)
            }
            
        except Exception as e:
            logger.error("Error importing transactions from CSV", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'transactions': [],
                'errors': []
            }
    
    async def import_holdings_from_csv(
        self, 
        file_content: bytes, 
        portfolio_id: int,
        user_id: int = 1
    ) -> Dict:
        """Import current holdings from CSV file."""
        try:
            # Parse CSV content
            csv_string = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_string))
            
            holdings = []
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Map CSV columns to holding fields
                    holding_data = await self._parse_holding_row(row, portfolio_id)
                    holdings.append(holding_data)
                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'error': str(e),
                        'data': row
                    })
            
            return {
                'success': True,
                'holdings': holdings,
                'total_parsed': len(holdings),
                'errors': errors,
                'error_count': len(errors)
            }
            
        except Exception as e:
            logger.error("Error importing holdings from CSV", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'holdings': [],
                'errors': []
            }
    
    async def export_transactions_to_csv(
        self, 
        transactions: List[Dict], 
        include_details: bool = True
    ) -> str:
        """Export transactions to CSV format."""
        try:
            output = io.StringIO()
            
            # Define CSV columns
            if include_details:
                fieldnames = [
                    'transaction_id', 'portfolio_id', 'portfolio_name', 
                    'asset_id', 'asset_symbol', 'asset_name',
                    'transaction_type', 'quantity', 'price', 'total_amount',
                    'fees', 'transaction_date', 'notes', 'created_at'
                ]
            else:
                fieldnames = [
                    'asset_symbol', 'transaction_type', 'quantity', 
                    'price', 'total_amount', 'fees', 'transaction_date', 'notes'
                ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for transaction in transactions:
                # Filter fields based on include_details
                if include_details:
                    row = {key: transaction.get(key, '') for key in fieldnames}
                else:
                    row = {
                        'asset_symbol': transaction.get('asset_symbol', ''),
                        'transaction_type': transaction.get('transaction_type', ''),
                        'quantity': transaction.get('quantity', ''),
                        'price': transaction.get('price', ''),
                        'total_amount': transaction.get('total_amount', ''),
                        'fees': transaction.get('fees', ''),
                        'transaction_date': transaction.get('transaction_date', ''),
                        'notes': transaction.get('notes', '')
                    }
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error("Error exporting transactions to CSV", error=str(e))
            raise
    
    async def export_holdings_to_csv(self, holdings: List[Dict]) -> str:
        """Export current holdings to CSV format."""
        try:
            output = io.StringIO()
            
            fieldnames = [
                'asset_symbol', 'asset_name', 'asset_type', 'sector',
                'quantity', 'average_cost', 'current_price', 'market_value',
                'unrealized_gain_loss', 'unrealized_gain_loss_percentage',
                'allocation_percentage'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for holding in holdings:
                row = {key: holding.get(key, '') for key in fieldnames}
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error("Error exporting holdings to CSV", error=str(e))
            raise
    
    async def export_portfolio_summary_to_csv(self, portfolio_data: Dict) -> str:
        """Export portfolio summary to CSV format."""
        try:
            output = io.StringIO()
            
            # Portfolio summary
            output.write("Portfolio Summary\n")
            output.write(f"Portfolio ID,{portfolio_data.get('portfolio_id', '')}\n")
            output.write(f"Current Value,{portfolio_data.get('current_value', '')}\n")
            output.write(f"Initial Value,{portfolio_data.get('initial_value', '')}\n")
            output.write(f"Total Return,{portfolio_data.get('total_return', '')}\n")
            output.write(f"Total Return %,{portfolio_data.get('total_return_percentage', '')}\n")
            output.write(f"Holdings Count,{portfolio_data.get('holdings_count', '')}\n")
            output.write(f"Last Updated,{portfolio_data.get('last_updated', '')}\n")
            output.write("\n")
            
            # Holdings details
            if 'holdings' in portfolio_data and portfolio_data['holdings']:
                output.write("Holdings Details\n")
                holdings_csv = await self.export_holdings_to_csv(portfolio_data['holdings'])
                output.write(holdings_csv)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error("Error exporting portfolio summary to CSV", error=str(e))
            raise
    
    async def import_from_excel(
        self, 
        file_content: bytes, 
        sheet_name: str = None,
        import_type: str = 'transactions'
    ) -> Dict:
        """Import data from Excel file."""
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name)
            
            # Convert to CSV format for processing
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue().encode('utf-8')
            
            # Use existing CSV import logic
            if import_type == 'transactions':
                return await self.import_transactions_from_csv(csv_content, portfolio_id=1)
            elif import_type == 'holdings':
                return await self.import_holdings_from_csv(csv_content, portfolio_id=1)
            else:
                raise ValueError(f"Unsupported import type: {import_type}")
            
        except Exception as e:
            logger.error("Error importing from Excel", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'transactions': [],
                'errors': []
            }
    
    async def export_to_excel(
        self, 
        data: Dict, 
        filename: str = "portfolio_export.xlsx"
    ) -> bytes:
        """Export data to Excel format."""
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Portfolio summary
                if 'portfolio_summary' in data:
                    summary_df = pd.DataFrame([data['portfolio_summary']])
                    summary_df.to_excel(writer, sheet_name='Portfolio Summary', index=False)
                
                # Holdings
                if 'holdings' in data:
                    holdings_df = pd.DataFrame(data['holdings'])
                    holdings_df.to_excel(writer, sheet_name='Holdings', index=False)
                
                # Transactions
                if 'transactions' in data:
                    transactions_df = pd.DataFrame(data['transactions'])
                    transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
                
                # Performance metrics
                if 'performance' in data:
                    performance_df = pd.DataFrame([data['performance']])
                    performance_df.to_excel(writer, sheet_name='Performance', index=False)
                
                # Allocation
                if 'allocation' in data:
                    if 'by_asset' in data['allocation']:
                        allocation_df = pd.DataFrame(data['allocation']['by_asset'])
                        allocation_df.to_excel(writer, sheet_name='Allocation by Asset', index=False)
                    
                    if 'by_sector' in data['allocation']:
                        sector_data = [
                            {'sector': k, 'value': v['value'], 'percentage': v['percentage']}
                            for k, v in data['allocation']['by_sector'].items()
                        ]
                        sector_df = pd.DataFrame(sector_data)
                        sector_df.to_excel(writer, sheet_name='Allocation by Sector', index=False)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error("Error exporting to Excel", error=str(e))
            raise
    
    async def _parse_transaction_row(self, row: Dict, portfolio_id: int) -> TransactionCreate:
        """Parse a single transaction row from CSV."""
        try:
            # Get asset by symbol
            asset_symbol = row.get('asset_symbol', '').upper()
            if not asset_symbol:
                raise ValueError("Asset symbol is required")
            
            asset = self.db.query(AssetModel).filter(
                AssetModel.symbol == asset_symbol
            ).first()
            
            if not asset:
                raise ValueError(f"Asset not found: {asset_symbol}")
            
            # Parse transaction data
            transaction_data = TransactionCreate(
                portfolio_id=portfolio_id,
                asset_id=asset.id,
                transaction_type=row.get('transaction_type', '').lower(),
                quantity=Decimal(str(row.get('quantity', '0'))),
                price=Decimal(str(row.get('price', '0'))),
                total_amount=Decimal(str(row.get('total_amount', '0'))),
                fees=Decimal(str(row.get('fees', '0'))),
                transaction_date=datetime.strptime(
                    row.get('transaction_date', ''), 
                    '%Y-%m-%d'
                ),
                notes=row.get('notes', '')
            )
            
            return transaction_data
            
        except Exception as e:
            raise ValueError(f"Error parsing transaction row: {str(e)}")
    
    async def _parse_holding_row(self, row: Dict, portfolio_id: int) -> Dict:
        """Parse a single holding row from CSV."""
        try:
            # Get asset by symbol
            asset_symbol = row.get('asset_symbol', '').upper()
            if not asset_symbol:
                raise ValueError("Asset symbol is required")
            
            asset = self.db.query(AssetModel).filter(
                AssetModel.symbol == asset_symbol
            ).first()
            
            if not asset:
                raise ValueError(f"Asset not found: {asset_symbol}")
            
            # Parse holding data
            holding_data = {
                'portfolio_id': portfolio_id,
                'asset_id': asset.id,
                'quantity': Decimal(str(row.get('quantity', '0'))),
                'average_cost': Decimal(str(row.get('average_cost', '0'))),
                'current_price': Decimal(str(row.get('current_price', '0'))) if row.get('current_price') else None,
                'market_value': Decimal(str(row.get('market_value', '0'))),
                'unrealized_gain_loss': Decimal(str(row.get('unrealized_gain_loss', '0'))),
                'unrealized_gain_loss_percentage': Decimal(str(row.get('unrealized_gain_loss_percentage', '0')))
            }
            
            return holding_data
            
        except Exception as e:
            raise ValueError(f"Error parsing holding row: {str(e)}")
    
    def get_transaction_template(self) -> str:
        """Get CSV template for transaction import."""
        template = """asset_symbol,transaction_type,quantity,price,total_amount,fees,transaction_date,notes
AAPL,buy,10,150.00,1500.00,0.00,2024-01-15,Initial purchase
GOOGL,buy,5,2500.00,12500.00,0.00,2024-01-20,Tech investment
MSFT,sell,5,300.00,1500.00,0.00,2024-02-01,Partial sale"""
        return template
    
    def get_holdings_template(self) -> str:
        """Get CSV template for holdings import."""
        template = """asset_symbol,quantity,average_cost,current_price,market_value,unrealized_gain_loss,unrealized_gain_loss_percentage
AAPL,10,150.00,160.00,1600.00,100.00,6.67
GOOGL,5,2500.00,2600.00,13000.00,500.00,2.00
MSFT,15,280.00,290.00,4350.00,150.00,3.57"""
        return template
