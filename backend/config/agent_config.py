"""
Configuration loading with environment variable support
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field


def substitute_env_vars(text: str) -> str:
    """替换字符串中的环境变量 ${VAR_NAME}"""
    pattern = re.compile(r"\$\{([^}]+)\}")

    def replace_var(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))  # 如果找不到环境变量，保持原样

    return pattern.sub(replace_var, text)


def extract_env_var_name(value: Optional[str]) -> Optional[str]:
    """当配置值仍为 ${VAR} 格式时提取变量名"""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return value[2:-1]
    return None


def load_config_with_env_vars(config_path: Path) -> Dict[str, Any]:
    """加载配置文件并替换环境变量"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()

    # 替换环境变量
    processed_content = substitute_env_vars(config_content)

    # 解析YAML
    try:
        config = yaml.safe_load(processed_content)
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"配置文件YAML格式错误: {e}")


class AgentConfig(BaseModel):
    model_name: str
    base_url: Optional[str] = None  # Custom base URL for different providers
    api_key: str
    decision_interval: int
    symbols: list[str]
    timeframes: list[str]
    trading_strategy: Optional[str] = None  # User-configurable trading strategy


class ExchangeConfig(BaseModel):
    name: str
    testnet: bool = True
    websocket_url: str
    rest_api_url: str
    testnet_websocket_url: str
    testnet_rest_api_url: str

    def get_websocket_url(self) -> str:
        """获取当前环境对应的WebSocket URL"""
        return self.testnet_websocket_url if self.testnet else self.websocket_url

    def get_rest_api_url(self) -> str:
        """获取当前环境对应的REST API URL"""
        return self.testnet_rest_api_url if self.testnet else self.rest_api_url

class ExchangeEntryConfig(BaseModel):
    """多交易所配置项"""

    ccxt_id: str
    auth_type: str = "api_key"
    credentials: Dict[str, str] = Field(default_factory=dict)
    testnet: bool = False
    sandbox: bool = False
    default_leverage: int = 1
    margin_mode: str = "cross"
    enable_rate_limit: bool = True
    timeout: int = 10000
    retries: int = 3
    options: Dict[str, Any] = Field(default_factory=dict)

    def build_ccxt_config(self) -> Dict[str, Any]:
        config = {
            "enableRateLimit": self.enable_rate_limit,
            "timeout": self.timeout,
            "retries": self.retries,
        }
        if self.options:
            config["options"] = self.options
        config.update(self.credentials)
        if self.testnet or self.sandbox:
            config["sandbox"] = True
        return config

class RiskConfig(BaseModel):
    max_position_size_percent: float
    max_daily_loss_percent: float
    stop_loss_percent: float


class AccountSnapshotConfig(BaseModel):
    enabled: bool = True
    interval_minutes: int = 15
    keep_days: int = 90


class LoggingConfig(BaseModel):
    level: str = "INFO"
    save_decisions: bool = True
    save_executions: bool = True
    save_snapshots: bool = True


class SystemConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    max_concurrent_decisions: int = 1


class AppConfig(BaseModel):
    agent: AgentConfig
    exchange: ExchangeConfig
    exchanges: Dict[str, ExchangeEntryConfig] = Field(default_factory=dict)
    default_risk: RiskConfig
    account_snapshot: AccountSnapshotConfig
    logging: LoggingConfig
    system: SystemConfig

    def validate_required_env_vars(self) -> list[str]:
        """检查必需的环境变量是否设置"""
        missing_vars = []

        if not self.agent.api_key or self.agent.api_key.startswith("${"):
            missing_vars.append("OPENAI_API_KEY")

        if self.exchanges:
            for name, exchange_entry in self.exchanges.items():
                for cred_key, cred_value in exchange_entry.credentials.items():
                    if not cred_value:
                        missing_vars.append(f"{name}.{cred_key}")
                        continue
                    env_var = extract_env_var_name(cred_value)
                    if env_var:
                        missing_vars.append(env_var)

        return missing_vars

    def is_testnet_mode(self) -> bool:
        """检查是否为测试模式"""
        return (
            self.exchange.testnet
            or any(entry.testnet or entry.sandbox for entry in self.exchanges.values())
        )

    def get_exchange_entry(self, name: Optional[str]) -> Optional[ExchangeEntryConfig]:
        if not name:
            return None
        name_lower = name.lower()
        for key, entry in self.exchanges.items():
            if key.lower() == name_lower:
                return entry
        return None

    def require_exchange_entry(self, name: str) -> ExchangeEntryConfig:
        entry = self.get_exchange_entry(name)
        if entry is None:
            raise ValueError(f"未找到交易所配置: {name}")
        return entry

    def get_default_leverage(self, name: Optional[str] = None) -> int:
        entry = self.get_exchange_entry(name or self.exchange.name)
        if entry and entry.default_leverage:
            return entry.default_leverage
        return 1


def load_app_config() -> AppConfig:
    """加载完整的应用配置"""
    config_path = Path(__file__).parent / "agent.yaml"

    # 加载并处理环境变量
    config_data = load_config_with_env_vars(config_path)

    # 创建配置对象
    return AppConfig(**config_data)


# 全局配置实例 - 延迟加载
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取应用配置（延迟加载）"""
    global config
    if config is None:
        config = load_app_config()
    return config


# 验证配置完整性
def validate_config():
    """验证配置的完整性，失败则退出程序"""
    cfg = get_config()
    errors = []

    # 检查必需配置项
    required_fields = [
        ("agent.model_name", cfg.agent.model_name),
        ("agent.api_key", cfg.agent.api_key),
        ("agent.decision_interval", cfg.agent.decision_interval),
        ("agent.symbols", cfg.agent.symbols),
        ("agent.timeframes", cfg.agent.timeframes),
        ("exchange.name", cfg.exchange.name),
        ("exchange.api_key", cfg.exchange.api_key),
        ("exchange.api_secret", cfg.exchange.api_secret),
    ]

    for field_name, field_value in required_fields:
        if not field_value:
            errors.append(f"缺少必需配置: {field_name}")

    # 检查数据类型和格式
    if not isinstance(cfg.agent.symbols, list) or len(cfg.agent.symbols) == 0:
        errors.append("agent.symbols 必须是非空列表")

    if not isinstance(cfg.agent.timeframes, list) or len(cfg.agent.timeframes) == 0:
        errors.append("agent.timeframes 必须是非空列表")

    # 检查时间框架格式
    valid_timeframes = [
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
    ]
    for tf in cfg.agent.timeframes:
        if tf not in valid_timeframes:
            errors.append(f"无效的时间框架: {tf}，支持的时间框架: {valid_timeframes}")

    # 检查API key格式
    if cfg.agent.api_key.startswith("${"):
        errors.append("agent.api_key 环境变量未正确设置")

    if cfg.exchange.api_key.startswith("${"):
        errors.append("exchange.api_key 环境变量未正确设置")

    if cfg.exchange.api_secret.startswith("${"):
        errors.append("exchange.api_secret 环境变量未正确设置")

    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"   - {error}")
        print("\n请检查 .env 文件和 config/agent.yaml 配置")
        print("系统将退出...")
        import sys

        sys.exit(1)

    print("✅ 配置验证通过")
