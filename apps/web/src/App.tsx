import { Link } from 'react-router-dom';
import { ThemeToggle } from './components/ThemeToggle';
import { KPICard } from './components/KPICard';
import { TimeseriesChart } from './components/TimeseriesChart';
import { CategoricalBarChart } from './components/CategoricalBarChart';

// Sample data for charts
const generateTimeseriesData = () => {
  const data = [];
  const highlightData = [];
  const startDate = new Date('2024-01-01');

  for (let i = 0; i < 12; i++) {
    const date = new Date(startDate);
    date.setMonth(i);

    const value = 50 + Math.random() * 30 + i * 2;
    data.push({ date, value });

    // Last 3 months are highlighted
    if (i >= 9) {
      highlightData.push({
        date,
        value,
        label: i === 11 ? `${value.toFixed(0)}` : undefined,
      });
    }
  }

  return { data, highlightData };
};

const categoryData = [
  { category: 'Product A', value: 245, highlight: true },
  { category: 'Product B', value: 189 },
  { category: 'Product C', value: 167 },
  { category: 'Product D', value: 143 },
  { category: 'Product E', value: 98 },
];

function App() {
  const { data, highlightData } = generateTimeseriesData();

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: 'var(--background)' }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <div>
              <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--text)' }}>
                Kearney Analytics Platform
              </h1>
              <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
                Data-driven insights with brand-locked design
              </p>
            </div>
            <ThemeToggle />
          </header>

          {/* KPI Cards Grid */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4" style={{ color: 'var(--text)' }}>
              Key Performance Indicators
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <KPICard
                title="Total Revenue"
                value="$2.4M"
                trend={{ direction: 'up', value: '+12.5%' }}
                insight="Revenue increased 12.5% compared to last quarter driven by Product A growth."
              />
              <KPICard
                title="Active Users"
                value="15,234"
                trend={{ direction: 'up', value: '+8.2%' }}
                insight="User base expanded across all segments with strongest growth in enterprise."
              />
              <KPICard
                title="Conversion Rate"
                value="3.8%"
                trend={{ direction: 'down', value: '-0.3%' }}
                insight="Slight decrease due to seasonal trends; optimization initiatives planned."
              />
            </div>
          </section>

          {/* Timeseries Chart */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4" style={{ color: 'var(--text)' }}>
              Revenue Trend
            </h2>
            <TimeseriesChart
              data={data}
              highlightData={highlightData}
              spotHighlight={{
                date: highlightData[highlightData.length - 1].date,
                label: 'Peak',
              }}
              title="Monthly Revenue (2024)"
              xLabel="Month"
              yLabel="Revenue ($K)"
              width={900}
              height={400}
            />
          </section>

          {/* Categorical Bar Chart */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4" style={{ color: 'var(--text)' }}>
              Product Performance
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <CategoricalBarChart
                data={categoryData}
                title="Sales by Product (Vertical)"
                yLabel="Sales ($K)"
                width={450}
                height={400}
                horizontal={false}
                sorted={true}
              />
              <CategoricalBarChart
                data={categoryData}
                title="Sales by Product (Horizontal)"
                xLabel="Sales ($K)"
                width={450}
                height={400}
                horizontal={true}
                sorted={true}
              />
            </div>
          </section>

          {/* Footer */}
          <footer className="mt-12 pt-8 border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="text-center mb-4">
              <Link
                to="/maps/d3-isochrone"
                className="inline-block px-6 py-3 rounded-lg font-semibold transition-all"
                style={{
                  backgroundColor: 'var(--emphasis)',
                  color: 'var(--text-inverse)',
                }}
              >
                View D3 Isochrone Map Demo
              </Link>
            </div>
            <p className="text-center text-sm" style={{ color: 'var(--text-muted)' }}>
              Kearney Design System - Phase 2 Implementation
            </p>
            <p className="text-center text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
              No emojis • No gridlines • Label-first • Spot color emphasis
            </p>
          </footer>
        </div>
      </div>
  );
}

export default App;
