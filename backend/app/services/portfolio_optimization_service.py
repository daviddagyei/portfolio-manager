"""
Portfolio Optimization Service
Implementation of Modern Portfolio Theory using PyPortfolioOpt
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from decimal import Decimal
from datetime import datetime, date, timedelta
import structlog
from sqlalchemy.orm import Session

# PyPortfolioOpt imports
from pypfopt import EfficientFrontier, DiscreteAllocation, get_latest_prices
from pypfopt import risk_models, expected_returns
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.expected_returns import mean_historical_return, ema_historical_return
from pypfopt.risk_models import CovarianceShrinkage, sample_cov
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt.plotting import plot_efficient_frontier
from pypfopt import objective_functions, base_optimizer

from app.models import Asset as AssetModel, PortfolioHolding, Portfolio as PortfolioModel
from app.services.market_data_service import MarketDataService
from app.core.database import get_db

logger = structlog.get_logger()


class PortfolioOptimizationService:
    """Advanced portfolio optimization service using Modern Portfolio Theory"""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_service = MarketDataService()
        
    async def get_asset_data(
        self, 
        asset_symbols: List[str], 
        lookback_days: int = 252
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch historical price data for assets
        
        Args:
            asset_symbols: List of asset symbols
            lookback_days: Number of days of historical data
            
        Returns:
            Tuple of (price_data, returns_data)
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)  # Extra buffer
            
            price_data = pd.DataFrame()
            
            for symbol in asset_symbols:
                try:
                    # Get historical prices
                    prices = await self.market_service.get_historical_prices(
                        symbol, start_date, end_date
                    )
                    
                    if prices is not None and len(prices) > 0:
                        # Convert to DataFrame if needed
                        if isinstance(prices, list):
                            price_series = pd.Series(
                                [p['close'] for p in prices],
                                index=[p['date'] for p in prices],
                                name=symbol
                            )
                        else:
                            price_series = prices.rename(symbol)
                            
                        price_data[symbol] = price_series
                        
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}", error=str(e))
                    continue
            
            if price_data.empty:
                raise ValueError("No price data available for optimization")
            
            # Calculate returns
            returns_data = price_data.pct_change().dropna()
            
            # Ensure minimum data points
            if len(returns_data) < 30:
                raise ValueError("Insufficient historical data for optimization")
            
            return price_data, returns_data
            
        except Exception as e:
            logger.error("Error fetching asset data", error=str(e))
            raise
    
    def calculate_efficient_frontier(
        self,
        returns_data: pd.DataFrame,
        risk_free_rate: float = 0.02,
        n_points: int = 100,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate efficient frontier
        
        Args:
            returns_data: Historical returns data
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            n_points: Number of points on the efficient frontier
            min_weight: Minimum weight constraint
            max_weight: Maximum weight constraint
            
        Returns:
            Dictionary with frontier data and key portfolios
        """
        try:
            # Calculate expected returns and covariance matrix
            mu = expected_returns.mean_historical_return(returns_data)
            S = risk_models.sample_cov(returns_data)
            
            # Create efficient frontier object
            ef = EfficientFrontier(mu, S)
            ef.add_constraint(lambda w: w >= min_weight)
            ef.add_constraint(lambda w: w <= max_weight)
            
            # Calculate frontier points
            target_returns = np.linspace(mu.min(), mu.max(), n_points)
            frontier_volatility = []
            frontier_returns = []
            frontier_weights = []
            
            for target_return in target_returns:
                try:
                    ef_copy = EfficientFrontier(mu, S)
                    ef_copy.add_constraint(lambda w: w >= min_weight)
                    ef_copy.add_constraint(lambda w: w <= max_weight)
                    
                    weights = ef_copy.efficient_return(target_return)
                    ret, vol, _ = ef_copy.portfolio_performance(risk_free_rate=risk_free_rate)
                    
                    frontier_returns.append(ret)
                    frontier_volatility.append(vol)
                    frontier_weights.append(weights)
                    
                except Exception:
                    continue
            
            # Calculate key portfolios
            key_portfolios = self._calculate_key_portfolios(mu, S, risk_free_rate, min_weight, max_weight)
            
            return {
                "frontier": {
                    "returns": frontier_returns,
                    "volatility": frontier_volatility,
                    "weights": frontier_weights
                },
                "key_portfolios": key_portfolios,
                "assets": list(returns_data.columns),
                "optimization_date": datetime.now().isoformat(),
                "risk_free_rate": risk_free_rate
            }
            
        except Exception as e:
            logger.error("Error calculating efficient frontier", error=str(e))
            raise
    
    def _calculate_key_portfolios(
        self,
        mu: pd.Series,
        S: pd.DataFrame,
        risk_free_rate: float,
        min_weight: float,
        max_weight: float
    ) -> Dict[str, Any]:
        """Calculate key optimization portfolios"""
        try:
            portfolios = {}
            
            # Maximum Sharpe Ratio Portfolio
            try:
                ef_sharpe = EfficientFrontier(mu, S)
                ef_sharpe.add_constraint(lambda w: w >= min_weight)
                ef_sharpe.add_constraint(lambda w: w <= max_weight)
                
                weights_sharpe = ef_sharpe.max_sharpe(risk_free_rate=risk_free_rate)
                ret_sharpe, vol_sharpe, sharpe_sharpe = ef_sharpe.portfolio_performance(risk_free_rate=risk_free_rate)
                
                portfolios["max_sharpe"] = {
                    "name": "Maximum Sharpe Ratio",
                    "weights": weights_sharpe,
                    "expected_return": ret_sharpe,
                    "volatility": vol_sharpe,
                    "sharpe_ratio": sharpe_sharpe
                }
            except Exception as e:
                logger.warning("Failed to calculate max Sharpe portfolio", error=str(e))
            
            # Minimum Volatility Portfolio
            try:
                ef_min_vol = EfficientFrontier(mu, S)
                ef_min_vol.add_constraint(lambda w: w >= min_weight)
                ef_min_vol.add_constraint(lambda w: w <= max_weight)
                
                weights_min_vol = ef_min_vol.min_volatility()
                ret_min_vol, vol_min_vol, sharpe_min_vol = ef_min_vol.portfolio_performance(risk_free_rate=risk_free_rate)
                
                portfolios["min_volatility"] = {
                    "name": "Minimum Volatility",
                    "weights": weights_min_vol,
                    "expected_return": ret_min_vol,
                    "volatility": vol_min_vol,
                    "sharpe_ratio": sharpe_min_vol
                }
            except Exception as e:
                logger.warning("Failed to calculate min volatility portfolio", error=str(e))
            
            # Maximum Return Portfolio (for given risk level)
            try:
                ef_max_ret = EfficientFrontier(mu, S)
                ef_max_ret.add_constraint(lambda w: w >= min_weight)
                ef_max_ret.add_constraint(lambda w: w <= max_weight)
                
                target_volatility = 0.15  # 15% volatility target
                weights_max_ret = ef_max_ret.efficient_risk(target_volatility)
                ret_max_ret, vol_max_ret, sharpe_max_ret = ef_max_ret.portfolio_performance(risk_free_rate=risk_free_rate)
                
                portfolios["max_return"] = {
                    "name": "Maximum Return (15% Vol Target)",
                    "weights": weights_max_ret,
                    "expected_return": ret_max_ret,
                    "volatility": vol_max_ret,
                    "sharpe_ratio": sharpe_max_ret
                }
            except Exception as e:
                logger.warning("Failed to calculate max return portfolio", error=str(e))
            
            # Equal Weight Portfolio
            try:
                n_assets = len(mu)
                equal_weights = {asset: 1/n_assets for asset in mu.index}
                
                # Calculate performance for equal weight
                weights_array = np.array(list(equal_weights.values()))
                ret_equal = np.dot(weights_array, mu)
                vol_equal = np.sqrt(np.dot(weights_array.T, np.dot(S, weights_array)))
                sharpe_equal = (ret_equal - risk_free_rate) / vol_equal
                
                portfolios["equal_weight"] = {
                    "name": "Equal Weight",
                    "weights": equal_weights,
                    "expected_return": ret_equal,
                    "volatility": vol_equal,
                    "sharpe_ratio": sharpe_equal
                }
            except Exception as e:
                logger.warning("Failed to calculate equal weight portfolio", error=str(e))
            
            return portfolios
            
        except Exception as e:
            logger.error("Error calculating key portfolios", error=str(e))
            return {}
    
    def optimize_portfolio(
        self,
        returns_data: pd.DataFrame,
        optimization_method: str = "max_sharpe",
        target_return: Optional[float] = None,
        target_volatility: Optional[float] = None,
        risk_free_rate: float = 0.02,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio for specific objective
        
        Args:
            returns_data: Historical returns data
            optimization_method: Optimization objective
            target_return: Target return (for efficient_return method)
            target_volatility: Target volatility (for efficient_risk method)
            risk_free_rate: Risk-free rate
            constraints: Additional constraints
            
        Returns:
            Optimized portfolio weights and metrics
        """
        try:
            # Calculate expected returns and covariance matrix
            mu = expected_returns.mean_historical_return(returns_data)
            S = risk_models.sample_cov(returns_data)
            
            # Create efficient frontier object
            ef = EfficientFrontier(mu, S)
            
            # Apply constraints
            if constraints:
                # Weight bounds
                if "min_weight" in constraints and "max_weight" in constraints:
                    ef.add_constraint(lambda w: w >= constraints["min_weight"])
                    ef.add_constraint(lambda w: w <= constraints["max_weight"])
                
                # Sector constraints
                if "sector_constraints" in constraints:
                    for sector, limits in constraints["sector_constraints"].items():
                        # This would need sector mapping - simplified for now
                        pass
                
                # Individual asset constraints
                if "asset_constraints" in constraints:
                    for asset, limits in constraints["asset_constraints"].items():
                        if asset in mu.index:
                            asset_idx = list(mu.index).index(asset)
                            if "min" in limits:
                                ef.add_constraint(lambda w: w[asset_idx] >= limits["min"])
                            if "max" in limits:
                                ef.add_constraint(lambda w: w[asset_idx] <= limits["max"])
            
            # Optimize based on method
            if optimization_method == "max_sharpe":
                weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
            elif optimization_method == "min_volatility":
                weights = ef.min_volatility()
            elif optimization_method == "efficient_return" and target_return:
                weights = ef.efficient_return(target_return)
            elif optimization_method == "efficient_risk" and target_volatility:
                weights = ef.efficient_risk(target_volatility)
            elif optimization_method == "max_quadratic_utility":
                weights = ef.max_quadratic_utility(risk_aversion=1)
            else:
                raise ValueError(f"Unknown optimization method: {optimization_method}")
            
            # Calculate portfolio performance
            ret, vol, sharpe = ef.portfolio_performance(risk_free_rate=risk_free_rate)
            
            # Clean weights (remove tiny positions)
            cleaned_weights = {k: v for k, v in weights.items() if abs(v) > 0.001}
            
            return {
                "optimization_method": optimization_method,
                "weights": cleaned_weights,
                "expected_return": ret,
                "volatility": vol,
                "sharpe_ratio": sharpe,
                "optimization_date": datetime.now().isoformat(),
                "risk_free_rate": risk_free_rate,
                "target_return": target_return,
                "target_volatility": target_volatility
            }
            
        except Exception as e:
            logger.error("Error optimizing portfolio", error=str(e))
            raise
    
    def calculate_discrete_allocation(
        self,
        weights: Dict[str, float],
        latest_prices: Dict[str, float],
        total_portfolio_value: float
    ) -> Dict[str, Any]:
        """
        Calculate discrete allocation for actual trading
        
        Args:
            weights: Portfolio weights
            latest_prices: Latest asset prices
            total_portfolio_value: Total portfolio value
            
        Returns:
            Discrete allocation and leftover cash
        """
        try:
            # Convert to pandas Series
            weights_series = pd.Series(weights)
            prices_series = pd.Series(latest_prices)
            
            # Calculate discrete allocation
            da = DiscreteAllocation(weights_series, prices_series, total_portfolio_value)
            allocation, leftover = da.greedy_portfolio()
            
            # Calculate allocation details
            total_allocated = sum(allocation[asset] * prices_series[asset] for asset in allocation)
            allocation_percentage = (total_allocated / total_portfolio_value) * 100
            
            return {
                "allocation": allocation,
                "leftover_cash": leftover,
                "total_allocated": total_allocated,
                "allocation_percentage": allocation_percentage,
                "total_value": total_portfolio_value
            }
            
        except Exception as e:
            logger.error("Error calculating discrete allocation", error=str(e))
            raise
    
    async def generate_rebalancing_suggestions(
        self,
        portfolio_id: int,
        target_weights: Dict[str, float],
        tolerance: float = 0.05
    ) -> Dict[str, Any]:
        """
        Generate rebalancing suggestions for a portfolio
        
        Args:
            portfolio_id: Portfolio ID
            target_weights: Target allocation weights
            tolerance: Rebalancing tolerance threshold
            
        Returns:
            Rebalancing suggestions and trade recommendations
        """
        try:
            # Get current portfolio holdings
            holdings = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.quantity > 0
            ).all()
            
            if not holdings:
                raise ValueError("No holdings found for portfolio")
            
            # Calculate current weights
            total_value = sum(h.market_value for h in holdings)
            current_weights = {}
            current_prices = {}
            
            for holding in holdings:
                asset = self.db.query(AssetModel).filter(AssetModel.id == holding.asset_id).first()
                if asset:
                    current_weights[asset.symbol] = float(holding.market_value / total_value)
                    current_prices[asset.symbol] = float(holding.current_price)
            
            # Calculate weight differences
            rebalancing_needed = False
            trades = []
            
            for symbol in target_weights:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights[symbol]
                weight_diff = target_weight - current_weight
                
                if abs(weight_diff) > tolerance:
                    rebalancing_needed = True
                    
                    # Calculate dollar amount to trade
                    dollar_diff = weight_diff * float(total_value)
                    
                    if symbol in current_prices:
                        shares_to_trade = dollar_diff / current_prices[symbol]
                        
                        trades.append({
                            "symbol": symbol,
                            "current_weight": current_weight,
                            "target_weight": target_weight,
                            "weight_difference": weight_diff,
                            "dollar_amount": dollar_diff,
                            "shares_to_trade": shares_to_trade,
                            "action": "buy" if dollar_diff > 0 else "sell",
                            "current_price": current_prices[symbol]
                        })
            
            # Check for assets not in target (should be sold)
            for symbol in current_weights:
                if symbol not in target_weights:
                    current_weight = current_weights[symbol]
                    dollar_amount = current_weight * float(total_value)
                    shares_to_trade = -dollar_amount / current_prices[symbol]
                    
                    trades.append({
                        "symbol": symbol,
                        "current_weight": current_weight,
                        "target_weight": 0.0,
                        "weight_difference": -current_weight,
                        "dollar_amount": -dollar_amount,
                        "shares_to_trade": shares_to_trade,
                        "action": "sell",
                        "current_price": current_prices[symbol]
                    })
                    rebalancing_needed = True
            
            return {
                "rebalancing_needed": rebalancing_needed,
                "current_weights": current_weights,
                "target_weights": target_weights,
                "trades": trades,
                "total_portfolio_value": float(total_value),
                "tolerance": tolerance,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error generating rebalancing suggestions", error=str(e))
            raise
    
    def run_scenario_analysis(
        self,
        weights: Dict[str, float],
        returns_data: pd.DataFrame,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run what-if scenario analysis on portfolio
        
        Args:
            weights: Portfolio weights
            returns_data: Historical returns data
            scenarios: List of scenario definitions
            
        Returns:
            Scenario analysis results
        """
        try:
            results = {}
            
            for i, scenario in enumerate(scenarios):
                scenario_name = scenario.get("name", f"Scenario_{i+1}")
                
                # Apply scenario modifications to returns
                modified_returns = returns_data.copy()
                
                if "return_shock" in scenario:
                    # Apply return shock to specific assets or all
                    shock = scenario["return_shock"]
                    if "assets" in shock:
                        for asset in shock["assets"]:
                            if asset in modified_returns.columns:
                                modified_returns[asset] += shock["value"]
                    else:
                        modified_returns += shock["value"]
                
                if "volatility_shock" in scenario:
                    # Increase volatility
                    vol_shock = scenario["volatility_shock"]
                    for col in modified_returns.columns:
                        std = modified_returns[col].std()
                        noise = np.random.normal(0, std * vol_shock["multiplier"], len(modified_returns))
                        modified_returns[col] += noise
                
                # Calculate portfolio performance under scenario
                weights_series = pd.Series([weights.get(col, 0) for col in modified_returns.columns], 
                                         index=modified_returns.columns)
                
                portfolio_returns = (modified_returns * weights_series).sum(axis=1)
                
                # Calculate metrics
                mean_return = portfolio_returns.mean() * 252  # Annualized
                volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized
                sharpe_ratio = mean_return / volatility if volatility > 0 else 0
                max_drawdown = (portfolio_returns.cumsum() - portfolio_returns.cumsum().expanding().max()).min()
                var_95 = portfolio_returns.quantile(0.05)
                
                results[scenario_name] = {
                    "description": scenario.get("description", ""),
                    "annualized_return": mean_return,
                    "volatility": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "var_95": var_95,
                    "total_return": (1 + portfolio_returns).prod() - 1
                }
            
            return {
                "scenarios": results,
                "base_portfolio_weights": weights,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error running scenario analysis", error=str(e))
            raise
    
    def calculate_risk_budgeting(
        self,
        returns_data: pd.DataFrame,
        risk_budget: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate risk budgeting allocation
        
        Args:
            returns_data: Historical returns data
            risk_budget: Target risk contribution by asset
            
        Returns:
            Risk budgeting portfolio weights
        """
        try:
            from pypfopt import risk_models
            from pypfopt.efficient_frontier import EfficientFrontier
            
            # Calculate covariance matrix
            S = risk_models.sample_cov(returns_data)
            
            # Risk budgeting optimization (simplified implementation)
            # This is a placeholder for more sophisticated risk budgeting
            n_assets = len(returns_data.columns)
            equal_risk_weights = {asset: 1/n_assets for asset in returns_data.columns}
            
            # Calculate expected returns
            mu = expected_returns.mean_historical_return(returns_data)
            
            # Create efficient frontier
            ef = EfficientFrontier(mu, S)
            weights = ef.min_volatility()  # Use min vol as approximation for equal risk
            
            # Calculate risk contributions
            weights_array = np.array(list(weights.values()))
            portfolio_vol = np.sqrt(np.dot(weights_array.T, np.dot(S, weights_array)))
            
            marginal_contrib = np.dot(S, weights_array) / portfolio_vol
            contrib = weights_array * marginal_contrib
            risk_contrib = contrib / contrib.sum()
            
            risk_contributions = {asset: contrib for asset, contrib in zip(returns_data.columns, risk_contrib)}
            
            return {
                "weights": weights,
                "risk_contributions": risk_contributions,
                "target_risk_budget": risk_budget,
                "portfolio_volatility": portfolio_vol
            }
            
        except Exception as e:
            logger.error("Error calculating risk budgeting", error=str(e))
            raise
