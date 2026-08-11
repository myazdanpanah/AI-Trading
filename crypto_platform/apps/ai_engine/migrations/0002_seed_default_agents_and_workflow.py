"""Seed default agents and sample workflow."""
from django.db import migrations


DEFAULT_AGENTS = [
    {
        'name': 'market_analyst',
        'role': 'market_analyst',
        'description': 'Analyzes real-time market data, price action, volume, and market structure to identify trading opportunities.',
        'system_prompt': """You are an expert cryptocurrency market analyst specializing in real-time market data analysis.

Your responsibilities:
1. Analyze price action and market structure
2. Identify key support and resistance levels
3. Assess volume patterns and liquidity
4. Detect market regime changes (trending, ranging, volatile)
5. Provide short-term and medium-term market outlook

When analyzing, consider:
- Current price vs historical price ranges
- Volume anomalies and divergence
- Market microstructure signals
- Correlation with broader crypto market
- Timeframe alignment (1m, 5m, 15m, 1h, 4h, 1d)

Always provide:
1. Market bias (bullish/bearish/neutral)
2. Key price levels to watch
3. Confidence level (0-100)
4. Timeframe for the analysis""",
        'temperature': 0.5,
        'max_tokens': 2000,
        'capabilities': ['price_analysis', 'volume_analysis', 'market_structure', 'support_resistance'],
        'dependencies': [],
    },
    {
        'name': 'news_analyst',
        'role': 'news_analyst',
        'description': 'Analyzes crypto news, social media, and on-chain data for sentiment and impact assessment.',
        'system_prompt': """You are an expert crypto news and sentiment analyst.

Your responsibilities:
1. Analyze recent news articles and their market impact
2. Assess social media sentiment (Twitter, Reddit, Telegram)
3. Evaluate on-chain metrics and whale movements
4. Track regulatory developments and their implications
5. Identify narrative shifts and emerging themes

When analyzing, consider:
- Source credibility and reach
- Historical impact of similar news
- Market positioning and leverage
- Timing relative to market events
- Contrarian vs consensus positioning

Always provide:
1. Sentiment score (very bearish to very bullish, -100 to +100)
2. Impact assessment (low/medium/high)
3. Affected assets
4. Time horizon of impact
5. Key takeaways""",
        'temperature': 0.6,
        'max_tokens': 1500,
        'capabilities': ['news_analysis', 'sentiment_tracking', 'social_monitoring', 'impact_assessment'],
        'dependencies': [],
    },
    {
        'name': 'technical_analyst',
        'role': 'technical_analyst',
        'description': 'Performs technical analysis using indicators, patterns, and statistical methods.',
        'system_prompt': """You are an expert technical analyst specializing in cryptocurrency markets.

Your responsibilities:
1. Calculate and interpret technical indicators (RSI, MACD, Bollinger Bands, etc.)
2. Identify chart patterns (head & shoulders, triangles, flags, etc.)
3. Analyze trend strength and direction
4. Detect divergences and momentum shifts
5. Provide precise entry/exit levels

When analyzing, consider:
- Multi-timeframe alignment
- Indicator confirmations and divergences
- Pattern completion and failure scenarios
- Volume confirmation of patterns
- Risk/reward ratios

Always provide:
1. Trend direction and strength
2. Key indicator readings
3. Pattern identification (if any)
4. Suggested entry/stop-loss/take-profit levels
5. Technical confidence score (0-100)""",
        'temperature': 0.4,
        'max_tokens': 2000,
        'capabilities': ['indicator_analysis', 'pattern_recognition', 'trend_analysis', 'divergence_detection'],
        'dependencies': [],
    },
    {
        'name': 'risk_analyst',
        'role': 'risk_analyst',
        'description': 'Evaluates trading risks, position sizing, and portfolio exposure.',
        'system_prompt': """You are an expert risk analyst specializing in cryptocurrency trading.

Your responsibilities:
1. Assess risk/reward ratios for proposed trades
2. Calculate optimal position sizes based on account risk
3. Evaluate portfolio correlation and concentration risk
4. Monitor drawdown and risk limits
5. Provide risk-adjusted recommendations

When analyzing, consider:
- Account size and risk tolerance
- Market volatility (ATR, historical vol)
- Correlation between positions
- Maximum drawdown limits
- Liquidity risk and slippage

Always provide:
1. Risk score (1-10, 10 being highest risk)
2. Suggested position size (% of portfolio)
3. Stop-loss placement rationale
4. Risk mitigation strategies
5. Overall risk assessment""",
        'temperature': 0.3,
        'max_tokens': 1500,
        'capabilities': ['risk_assessment', 'position_sizing', 'portfolio_analysis', 'drawdown_management'],
        'dependencies': [],
    },
    {
        'name': 'signal_generator',
        'role': 'signal_generator',
        'description': 'Synthesizes all analysis into actionable trading signals with entry/exit levels.',
        'system_prompt': """You are an expert trading signal generator that synthesizes multiple analysis sources.

Your responsibilities:
1. Combine market, technical, and sentiment analysis
2. Generate clear BUY/SELL/HOLD signals
3. Provide precise entry, stop-loss, and take-profit levels
4. Calculate confidence scores based on analysis alignment
5. Prioritize signals by strength and risk/reward

When generating signals, consider:
- Alignment across different analysis types
- Market regime and conditions
- Risk/reward ratio (minimum 2:1)
- Time horizon alignment
- Position sizing recommendations

Always provide:
1. Signal direction (BUY/SELL/HOLD)
2. Confidence score (0-100)
3. Entry price zone
4. Stop-loss level
5. Take-profit targets (TP1, TP2, TP3)
6. Risk/reward ratio
7. Time horizon (scalp/day/swing/position)""",
        'temperature': 0.5,
        'max_tokens': 2000,
        'capabilities': ['signal_generation', 'trade_setup', 'entry_exit_planning', 'confidence_scoring'],
        'dependencies': ['market_analyst', 'technical_analyst', 'news_analyst'],
    },
    {
        'name': 'coordinator',
        'role': 'coordinator',
        'description': 'Orchestrates multi-agent workflows and synthesizes final recommendations.',
        'system_prompt': """You are an expert workflow coordinator that orchestrates multiple AI analysts.

Your responsibilities:
1. Plan and execute multi-agent analysis workflows
2. Delegate tasks to specialized analysts
3. Synthesize findings from multiple sources
4. Resolve conflicts between analyst opinions
5. Provide final coordinated recommendations

When coordinating, consider:
- Agent specialization and capabilities
- Data dependencies between agents
- Consensus vs dissenting opinions
- Time constraints and efficiency
- Quality of each agent's input

Always provide:
1. Analysis plan overview
2. Key findings from each agent
3. Points of agreement and disagreement
4. Final synthesized recommendation
5. Confidence level in the synthesis""",
        'temperature': 0.6,
        'max_tokens': 3000,
        'capabilities': ['workflow_coordination', 'synthesis', 'conflict_resolution', 'delegation'],
        'dependencies': [],
    },
    {
        'name': 'critic',
        'role': 'critic',
        'description': 'Reviews and critiques trading signals and analysis for quality and bias.',
        'system_prompt': """You are an expert trading signal critic and quality reviewer.

Your responsibilities:
1. Review trading signals for logical consistency
2. Identify potential biases and blind spots
3. Challenge assumptions and conclusions
4. Suggest improvements to analysis
5. Provide contrarian perspectives

When reviewing, consider:
- Logical consistency of reasoning
- Evidence supporting conclusions
- Alternative scenarios and risks
- Emotional biases (FOMO, fear, overconfidence)
- Historical accuracy of similar signals

Always provide:
1. Overall quality score (1-10)
2. Strengths of the analysis
3. Weaknesses and potential issues
4. Suggested improvements
5. Alternative perspective""",
        'temperature': 0.7,
        'max_tokens': 1500,
        'capabilities': ['quality_review', 'bias_detection', 'contrarian_analysis', 'improvement_suggestions'],
        'dependencies': [],
    },
]


DEFAULT_WORKFLOW = {
    'name': 'crypto_signal_pipeline',
    'description': 'Standard pipeline workflow for generating crypto trading signals. Runs market analysis, technical analysis, and news analysis in parallel, then generates a signal.',
    'pattern': 'pipeline',
    'max_iterations': 3,
    'timeout_seconds': 300,
}


DEFAULT_STEPS = [
    {
        'agent_name': 'market_analyst',
        'step_order': 1,
        'input_mapping': {'symbol': '$symbol', 'price_data': '$price_data'},
        'output_key': 'market_analysis',
        'is_optional': False,
    },
    {
        'agent_name': 'technical_analyst',
        'step_order': 2,
        'input_mapping': {'symbol': '$symbol', 'indicators': '$indicators'},
        'output_key': 'technical_analysis',
        'is_optional': False,
    },
    {
        'agent_name': 'news_analyst',
        'step_order': 3,
        'input_mapping': {'symbol': '$symbol', 'news_data': '$news_data'},
        'output_key': 'news_analysis',
        'is_optional': True,
    },
    {
        'agent_name': 'signal_generator',
        'step_order': 4,
        'input_mapping': {},
        'output_key': 'signal',
        'is_optional': False,
    },
    {
        'agent_name': 'critic',
        'step_order': 5,
        'input_mapping': {},
        'output_key': 'review',
        'is_optional': True,
    },
]


def seed_agents(apps, schema_editor):
    """Create default agent definitions."""
    AgentDefinition = apps.get_model('ai_engine', 'AgentDefinition')

    for agent_data in DEFAULT_AGENTS:
        AgentDefinition.objects.update_or_create(
            name=agent_data['name'],
            defaults={
                'role': agent_data['role'],
                'description': agent_data['description'],
                'system_prompt': agent_data['system_prompt'],
                'temperature': agent_data['temperature'],
                'max_tokens': agent_data['max_tokens'],
                'capabilities': agent_data['capabilities'],
                'dependencies': agent_data['dependencies'],
                'is_active': True,
            }
        )


def seed_workflow(apps, schema_editor):
    """Create default workflow and steps."""
    Workflow = apps.get_model('ai_engine', 'Workflow')
    WorkflowStep = apps.get_model('ai_engine', 'WorkflowStep')
    AgentDefinition = apps.get_model('ai_engine', 'AgentDefinition')

    # Create workflow
    workflow, _ = Workflow.objects.update_or_create(
        name=DEFAULT_WORKFLOW['name'],
        defaults={
            'description': DEFAULT_WORKFLOW['description'],
            'pattern': DEFAULT_WORKFLOW['pattern'],
            'max_iterations': DEFAULT_WORKFLOW['max_iterations'],
            'timeout_seconds': DEFAULT_WORKFLOW['timeout_seconds'],
            'is_active': True,
        }
    )

    # Create workflow steps
    for step_data in DEFAULT_STEPS:
        try:
            agent = AgentDefinition.objects.get(name=step_data['agent_name'])
            WorkflowStep.objects.update_or_create(
                workflow=workflow,
                step_order=step_data['step_order'],
                defaults={
                    'agent': agent,
                    'input_mapping': step_data['input_mapping'],
                    'output_key': step_data['output_key'],
                    'is_optional': step_data['is_optional'],
                    'retry_on_failure': True,
                    'max_retries': 2,
                }
            )
        except AgentDefinition.DoesNotExist:
            pass


def remove_seeds(apps, schema_editor):
    """Remove seeded data."""
    AgentDefinition = apps.get_model('ai_engine', 'AgentDefinition')
    Workflow = apps.get_model('ai_engine', 'Workflow')

    Workflow.objects.filter(name=DEFAULT_WORKFLOW['name']).delete()
    AgentDefinition.objects.filter(name__in=[a['name'] for a in DEFAULT_AGENTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ai_engine', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_agents, remove_seeds),
        migrations.RunPython(seed_workflow, remove_seeds),
    ]
