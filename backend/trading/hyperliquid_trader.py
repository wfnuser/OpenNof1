"""
Hyperliquid Trader implementation via CCXT
"""
from datetime import datetime
from typing import Dict, List, Optional

import ccxt  # type: ignore

from trading.interface import Balance, ExchangeTrader, Position
from utils.logger import logger


class HyperliquidTrader(ExchangeTrader):
    """Hyperliquid 交易器实现"""

    def __init__(self):
        from config.settings import config

        exchange_entry = config.get_exchange_entry("hyperliquid")

        if exchange_entry is None:
            raise ValueError("配置中未启用 Hyperliquid 交易所")

        credentials = exchange_entry.credentials or {}
        wallet_address = credentials.get("wallet_address") or credentials.get("walletAddress")
        private_key = credentials.get("private_key") or credentials.get("privateKey")

        if not wallet_address or not private_key:
            raise ValueError("Hyperliquid 配置缺少钱包地址或私钥")

        self.user_address = credentials.get("user")

        exchange_config: Dict[str, object] = exchange_entry.build_ccxt_config()
        exchange_config["walletAddress"] = wallet_address
        exchange_config["privateKey"] = private_key

        self.default_leverage = exchange_entry.default_leverage
        self.default_slippage = float(exchange_entry.options.get("slippage", 0.05)) if exchange_entry.options else 0.05
        self.exchange = ccxt.hyperliquid(exchange_config)
        self.exchange.options.setdefault("slippage", self.default_slippage)
        self.exchange.options.setdefault("defaultSlippage", self.default_slippage)

        # Hyperliquid 没有官方测试网，但允许 sandbox 参数
        if exchange_entry.testnet:
            try:
                self.exchange.set_sandbox_mode(True)
            except Exception:
                logger.warning("Hyperliquid 不支持 sandbox/testnet 模式")

        try:
            self.exchange.load_markets()
        except Exception as exc:
            logger.warning(f"加载 Hyperliquid 市场数据失败: {exc}")

        logger.info("初始化 Hyperliquid 交易器成功")

    async def get_balance(self) -> Balance:
        params = {"user": self.user_address} if self.user_address else {}
        balance = self.exchange.fetch_balance(params)
        usdc = balance.get("USDC", {})

        total = float(usdc.get("total") or 0)
        free = float(usdc.get("free") or (total - float(usdc.get("used") or 0)))

        positions = await self.get_positions()
        unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)

        timestamp = balance.get("timestamp")
        balance_time = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()

        return Balance(
            total_balance=total,
            available_balance=free,
            margin_balance=total + unrealized_pnl,
            unrealized_pnl=unrealized_pnl,
            currency="USDC",
            timestamp=balance_time,
        )

    async def get_positions(self) -> List[Position]:
        params = {"user": self.user_address} if self.user_address else {}
        positions = self.exchange.fetch_positions(params=params)
        active_positions: List[Position] = []

        for pos in positions:
            contracts = float(pos.get("contracts") or 0)
            if contracts <= 0:
                continue

            symbol = pos.get("symbol")
            timestamp = pos.get("timestamp")
            position_time = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()

            active_positions.append(
                Position(
                    symbol=symbol,
                    side=str(pos.get("side", "")).upper(),
                    size=contracts,
                    entry_price=float(pos.get("entryPrice") or 0),
                    mark_price=float(pos.get("markPrice") or 0),
                    unrealized_pnl=float(pos.get("unrealizedPnl") or 0),
                    percentage_pnl=float(pos.get("percentage") or 0),
                    leverage=float(pos.get("leverage") or self.default_leverage),
                    margin=float(pos.get("initialMargin") or pos.get("collateral") or 0),
                    timestamp=position_time,
                )
            )

        return active_positions

    async def open_long(
        self,
        symbol: str,
        quantity: float,
        leverage: int = 1,
        stop_loss_price: float = None,
        take_profit_price: float = None,
    ):
        logger.info(f"Hyperliquid 开多 {symbol} 数量: {quantity} 杠杆: {leverage}x")
        await self.set_leverage(symbol, leverage)

        market_price = await self._get_reference_price(symbol)
        params = self._build_order_params(stop_loss_price, take_profit_price, market_price)
        exchange_symbol = symbol
        params.setdefault("slippage", self.default_slippage)
        return self.exchange.create_order(exchange_symbol, 'market', 'buy', quantity, market_price, params)

    async def open_short(
        self,
        symbol: str,
        quantity: float,
        leverage: int = 1,
        stop_loss_price: float = None,
        take_profit_price: float = None,
    ):
        logger.info(f"Hyperliquid 开空 {symbol} 数量: {quantity} 杠杆: {leverage}x")
        await self.set_leverage(symbol, leverage)

        market_price = await self._get_reference_price(symbol)
        params = self._build_order_params(stop_loss_price, take_profit_price, market_price)
        exchange_symbol = symbol
        params.setdefault("slippage", self.default_slippage)
        return self.exchange.create_order(exchange_symbol, 'market', 'sell', quantity, market_price, params)

    async def close_long(self, symbol: str, quantity: float = 0):
        positions = await self.get_positions()
        long_position = next(
            (pos for pos in positions if pos.symbol == symbol and pos.side == "LONG"),
            None,
        )

        if not long_position:
            raise ValueError(f"没有找到 {symbol} 的多头持仓")

        size = long_position.size if quantity == 0 else quantity
        if size > long_position.size:
            raise ValueError("平仓数量超过当前多仓数量")

        await self.cancel_all_orders(symbol)
        exchange_symbol = symbol
        price = await self._get_reference_price(symbol)
        params = {"reduceOnly": True, "slippage": self.default_slippage, "price": price}
        return self.exchange.create_order(
            exchange_symbol,
            "market",
            "sell",
            size,
            price,
            params,
        )

    async def close_short(self, symbol: str, quantity: float = 0):
        positions = await self.get_positions()
        short_position = next(
            (pos for pos in positions if pos.symbol == symbol and pos.side == "SHORT"),
            None,
        )

        if not short_position:
            raise ValueError(f"没有找到 {symbol} 的空头持仓")

        size = short_position.size if quantity == 0 else quantity
        if size > short_position.size:
            raise ValueError("平仓数量超过当前空仓数量")

        await self.cancel_all_orders(symbol)
        exchange_symbol = symbol
        price = await self._get_reference_price(symbol)
        params = {"reduceOnly": True, "slippage": self.default_slippage, "price": price}
        return self.exchange.create_order(
            exchange_symbol,
            "market",
            "buy",
            size,
            price,
            params,
        )

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        try:
            exchange_symbol = symbol
            self.exchange.set_leverage(leverage, exchange_symbol)
            return True
        except Exception as exc:
            logger.error(f"设置 Hyperliquid 杠杆失败 {symbol}: {exc}")
            return False

    async def set_margin_mode(self, symbol: str, is_cross_margin: bool) -> bool:
        try:
            exchange_symbol = symbol
            margin_mode = "cross" if is_cross_margin else "isolated"
            params = {"leverage": self.default_leverage}
            self.exchange.set_margin_mode(margin_mode, exchange_symbol, params)
            return True
        except Exception as exc:
            logger.error(f"设置 Hyperliquid 保证金模式失败 {symbol}: {exc}")
            return False

    async def get_market_price(self, symbol: str) -> float:
        try:
            exchange_symbol = symbol
            ticker = self.exchange.fetch_ticker(exchange_symbol)
            return float(ticker.get("last") or 0.0)
        except Exception as exc:
            logger.error(f"获取 Hyperliquid 市场价格失败 {symbol}: {exc}")
            return 0.0

    async def cancel_all_orders(self, symbol: str) -> bool:
        try:
            exchange_symbol = symbol
            params = {"user": self.user_address} if self.user_address else {}
            open_orders = self.exchange.fetch_open_orders(exchange_symbol, params=params)
            if not open_orders:
                return True
            order_ids = [order["id"] for order in open_orders if order.get("id")]
            if not order_ids:
                return True
            self.exchange.cancel_orders(order_ids, exchange_symbol)
            return True
        except Exception as exc:
            logger.error(f"取消 Hyperliquid 挂单失败 {symbol}: {exc}")
            return False

    def format_quantity(self, symbol: str, quantity: float) -> str:
        try:
            exchange_symbol = symbol
            markets = self.exchange.load_markets()
            market = markets.get(exchange_symbol)
            if not market:
                return f"{quantity}"
            precision = market.get("precision", {}).get("amount")
            if precision is None:
                return f"{quantity}"
            return f"{quantity:.{precision}f}"
        except Exception:
            return f"{quantity}"

    def get_exchange_name(self) -> str:
        return "hyperliquid"

    def _build_order_params(self, stop_loss: Optional[float], take_profit: Optional[float], price: float) -> Dict[str, float]:
        params: Dict[str, float] = {"price": price}
        if stop_loss is not None:
            params["stopLossPrice"] = stop_loss
        if take_profit is not None:
            params["takeProfitPrice"] = take_profit
        params.setdefault("slippage", self.default_slippage)
        return params

    async def _get_reference_price(self, symbol: str) -> float:
        price = await self.get_market_price(symbol)
        if price <= 0:
            raise ValueError(f"无法获取 {symbol} 的有效价格")
        return price
