WITH expected_strategies(strategy_name) AS (
  VALUES
    ('research_v2_historical'),
    ('research_v2_live'),
    ('early_discovery'),
    ('continuation_runner'),
    ('premium_runner'),
    ('confirmed_runner')
)
SELECT
  expected_strategies.strategy_name,
  COUNT(strategy_research_view.strategy_name) AS rows,
  COALESCE(SUM(strategy_research_view.filter_passed), 0) AS passed
FROM expected_strategies
LEFT JOIN strategy_research_view
  ON strategy_research_view.strategy_name = expected_strategies.strategy_name
GROUP BY expected_strategies.strategy_name
ORDER BY expected_strategies.strategy_name;
