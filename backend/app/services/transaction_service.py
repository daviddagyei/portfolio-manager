from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, date
from decimal import Decimal

from app.models import Transaction as TransactionModel, Portfolio as PortfolioModel, Asset as AssetModel
from app.schemas import (
    TransactionCreate, TransactionUpdate, Transaction, TransactionWithDetails
)


class TransactionService:
    """Service class for transaction operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        portfolio_id: Optional[int] = None,
        asset_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Tuple[List[TransactionWithDetails], int]:
        """Get transactions with optional filtering."""
        query = self.db.query(
            TransactionModel,
            AssetModel.symbol,
            AssetModel.name,
            PortfolioModel.name.label('portfolio_name')
        ).join(
            AssetModel, TransactionModel.asset_id == AssetModel.id
        ).join(
            PortfolioModel, TransactionModel.portfolio_id == PortfolioModel.id
        )
        
        # Apply filters
        if user_id:
            query = query.filter(TransactionModel.user_id == user_id)
        if portfolio_id:
            query = query.filter(TransactionModel.portfolio_id == portfolio_id)
        if asset_id:
            query = query.filter(TransactionModel.asset_id == asset_id)
        if transaction_type:
            query = query.filter(TransactionModel.transaction_type == transaction_type)
        if start_date:
            query = query.filter(TransactionModel.transaction_date >= start_date)
        if end_date:
            query = query.filter(TransactionModel.transaction_date <= end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        results = query.order_by(
            TransactionModel.transaction_date.desc(),
            TransactionModel.id.desc()
        ).offset(skip).limit(limit).all()
        
        # Convert to TransactionWithDetails
        transactions = []
        for transaction, asset_symbol, asset_name, portfolio_name in results:
            transaction_dict = {
                **transaction.__dict__,
                'asset_symbol': asset_symbol,
                'asset_name': asset_name,
                'portfolio_name': portfolio_name
            }
            transactions.append(TransactionWithDetails(**transaction_dict))
        
        return transactions, total
    
    async def get_transaction(self, transaction_id: int, user_id: Optional[int] = None) -> Optional[Transaction]:
        """Get a specific transaction by ID."""
        query = self.db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id
        )
        
        if user_id:
            query = query.filter(TransactionModel.user_id == user_id)
        
        transaction = query.first()
        return Transaction.from_orm(transaction) if transaction else None
    
    async def create_transaction(self, transaction_data: TransactionCreate, user_id: int = 1) -> Transaction:
        """Create a new transaction."""
        # Validate portfolio and asset exist
        portfolio = self.db.query(PortfolioModel).filter(
            PortfolioModel.id == transaction_data.portfolio_id
        ).first()
        
        if not portfolio:
            raise ValueError(f"Portfolio with ID {transaction_data.portfolio_id} not found")
        
        asset = self.db.query(AssetModel).filter(
            AssetModel.id == transaction_data.asset_id
        ).first()
        
        if not asset:
            raise ValueError(f"Asset with ID {transaction_data.asset_id} not found")
        
        # Create transaction
        transaction = TransactionModel(
            **transaction_data.dict(),
            user_id=user_id  # Placeholder user ID
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        # Update portfolio holdings
        await self._update_portfolio_holdings(transaction)
        
        return Transaction.from_orm(transaction)
    
    async def update_transaction(
        self, 
        transaction_id: int, 
        transaction_update: TransactionUpdate,
        user_id: Optional[int] = None
    ) -> Optional[Transaction]:
        """Update a transaction."""
        query = self.db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id
        )
        
        if user_id:
            query = query.filter(TransactionModel.user_id == user_id)
        
        transaction = query.first()
        
        if not transaction:
            return None
        
        # Store old values for reverting holdings
        old_transaction = Transaction.from_orm(transaction)
        
        # Update transaction
        update_data = transaction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        
        # Update portfolio holdings (revert old and apply new)
        await self._revert_portfolio_holdings(old_transaction)
        await self._update_portfolio_holdings(transaction)
        
        return Transaction.from_orm(transaction)
    
    async def delete_transaction(self, transaction_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a transaction."""
        query = self.db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id
        )
        
        if user_id:
            query = query.filter(TransactionModel.user_id == user_id)
        
        transaction = query.first()
        
        if not transaction:
            return False
        
        # Revert portfolio holdings
        await self._revert_portfolio_holdings(Transaction.from_orm(transaction))
        
        self.db.delete(transaction)
        self.db.commit()
        
        return True
    
    async def get_portfolio_transactions(
        self,
        portfolio_id: int,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> Tuple[List[TransactionWithDetails], int]:
        """Get all transactions for a specific portfolio."""
        return await self.get_transactions(
            skip=skip,
            limit=limit,
            user_id=user_id,
            portfolio_id=portfolio_id
        )
    
    async def bulk_create_transactions(
        self,
        transactions: List[TransactionCreate],
        user_id: int = 1
    ) -> List[Transaction]:
        """Create multiple transactions in bulk."""
        created_transactions = []
        
        for transaction_data in transactions:
            try:
                transaction = await self.create_transaction(transaction_data, user_id)
                created_transactions.append(transaction)
            except Exception as e:
                # Log error but continue with other transactions
                print(f"Error creating transaction: {e}")
                continue
        
        return created_transactions
    
    async def _update_portfolio_holdings(self, transaction: TransactionModel):
        """Update portfolio holdings based on transaction."""
        from app.models import PortfolioHolding
        
        # Get or create holding
        holding = self.db.query(PortfolioHolding).filter(
            and_(
                PortfolioHolding.portfolio_id == transaction.portfolio_id,
                PortfolioHolding.asset_id == transaction.asset_id
            )
        ).first()
        
        if not holding:
            holding = PortfolioHolding(
                portfolio_id=transaction.portfolio_id,
                asset_id=transaction.asset_id,
                quantity=Decimal('0'),
                average_cost=Decimal('0'),
                market_value=Decimal('0'),
                unrealized_gain_loss=Decimal('0'),
                unrealized_gain_loss_percentage=Decimal('0')
            )
            self.db.add(holding)
        
        # Update holdings based on transaction type
        if transaction.transaction_type in ['buy', 'transfer_in']:
            old_quantity = holding.quantity
            old_value = old_quantity * holding.average_cost
            
            new_quantity = old_quantity + transaction.quantity
            new_value = old_value + transaction.total_amount
            
            if new_quantity > 0:
                holding.average_cost = new_value / new_quantity
            
            holding.quantity = new_quantity
            
        elif transaction.transaction_type in ['sell', 'transfer_out']:
            holding.quantity = holding.quantity - transaction.quantity
            
            # If quantity becomes zero or negative, reset average cost
            if holding.quantity <= 0:
                holding.quantity = Decimal('0')
                holding.average_cost = Decimal('0')
        
        # Update market value (will be updated with real-time prices later)
        holding.market_value = holding.quantity * (holding.current_price or holding.average_cost)
        
        # Calculate unrealized gain/loss
        if holding.quantity > 0 and holding.current_price:
            holding.unrealized_gain_loss = holding.market_value - (holding.quantity * holding.average_cost)
            holding.unrealized_gain_loss_percentage = (
                holding.unrealized_gain_loss / (holding.quantity * holding.average_cost)
            ) * 100
        else:
            holding.unrealized_gain_loss = Decimal('0')
            holding.unrealized_gain_loss_percentage = Decimal('0')
        
        self.db.commit()
    
    async def _revert_portfolio_holdings(self, transaction: Transaction):
        """Revert portfolio holdings based on transaction (used for updates/deletes)."""
        from app.models import PortfolioHolding
        
        # Get holding
        holding = self.db.query(PortfolioHolding).filter(
            and_(
                PortfolioHolding.portfolio_id == transaction.portfolio_id,
                PortfolioHolding.asset_id == transaction.asset_id
            )
        ).first()
        
        if not holding:
            return
        
        # Revert holdings based on transaction type
        if transaction.transaction_type in ['buy', 'transfer_in']:
            old_quantity = holding.quantity
            old_value = old_quantity * holding.average_cost
            
            new_quantity = old_quantity - transaction.quantity
            new_value = old_value - transaction.total_amount
            
            if new_quantity > 0:
                holding.average_cost = new_value / new_quantity
            else:
                holding.average_cost = Decimal('0')
            
            holding.quantity = new_quantity
            
        elif transaction.transaction_type in ['sell', 'transfer_out']:
            # Add back the sold quantity
            holding.quantity = holding.quantity + transaction.quantity
        
        # Update market value
        holding.market_value = holding.quantity * (holding.current_price or holding.average_cost)
        
        # Recalculate unrealized gain/loss
        if holding.quantity > 0 and holding.current_price:
            holding.unrealized_gain_loss = holding.market_value - (holding.quantity * holding.average_cost)
            holding.unrealized_gain_loss_percentage = (
                holding.unrealized_gain_loss / (holding.quantity * holding.average_cost)
            ) * 100
        else:
            holding.unrealized_gain_loss = Decimal('0')
            holding.unrealized_gain_loss_percentage = Decimal('0')
        
        self.db.commit()
