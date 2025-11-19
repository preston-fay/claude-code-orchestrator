import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { KPICard } from '../components/KPICard';
import { TimeseriesChart } from '../components/TimeseriesChart';
import { CategoricalBarChart } from '../components/CategoricalBarChart';

interface ClientTheme {
  client: {
    slug: string;
    name: string;
    logo?: string;
  };
  colors?: {
    light?: Record<string, string>;
    dark?: Record<string, string>;
  };
  typography?: {
    fontFamilyPrimary?: string;
    fontSizeBase?: string;
    fontWeightNormal?: number;
    fontWeightBold?: number;
  };
  constraints: {
    allowEmojis: false;
    allowGridlines: false;
    labelFirst: true;
  };
}

const defaultTheme: ClientTheme = {
  client: {
    slug: 'new-client',
    name: 'New Client',
  },
  colors: {
    light: {
      primary: '#7823DC',
      emphasis: '#9150E1',  // Approved Kearney purple
    },
    dark: {
      primary: '#AF7DEB',   // Approved dark theme purple
      emphasis: '#C8A5F0',  // Approved lighter purple for dark mode
    },
  },
  typography: {
    fontFamilyPrimary: 'Inter, Arial, sans-serif',
  },
  constraints: {
    allowEmojis: false,
    allowGridlines: false,
    labelFirst: true,
  },
};

export function ThemeStudio() {
  const { theme, setTheme } = useTheme();
  const [clientTheme, setClientTheme] = useState<ClientTheme>(defaultTheme);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [clients, setClients] = useState<string[]>([]);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Load available clients
  useEffect(() => {
    fetch('/api/theme/clients')
      .then((res) => res.json())
      .then((data) => setClients(data.clients || []))
      .catch(console.error);
  }, []);

  // Load client theme
  const loadClientTheme = async (slug: string) => {
    try {
      const res = await fetch(`/api/theme/clients/${slug}`);
      if (res.ok) {
        const data = await res.json();
        setClientTheme(data);
        setSelectedClient(slug);
      }
    } catch (error) {
      console.error('Failed to load client theme:', error);
    }
  };

  // Save client theme
  const saveClientTheme = async () => {
    setSaveStatus('saving');
    try {
      const res = await fetch(`/api/theme/clients/${clientTheme.client.slug}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(clientTheme),
      });

      if (res.ok) {
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);

        // Refresh clients list
        const clientsRes = await fetch('/api/theme/clients');
        const clientsData = await clientsRes.json();
        setClients(clientsData.clients || []);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error('Failed to save theme:', error);
      setSaveStatus('error');
    }
  };

  // Validate theme
  const validateTheme = async () => {
    try {
      const res = await fetch('/api/theme/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(clientTheme),
      });

      const data = await res.json();
      if (data.valid) {
        alert('Theme is valid!');
      } else {
        alert(`Theme validation failed:\n${data.errors.join('\n')}`);
      }
    } catch (error) {
      alert('Validation failed: ' + error);
    }
  };

  // Update color
  const updateColor = (colorMode: 'light' | 'dark', colorKey: string, value: string) => {
    setClientTheme((prev) => ({
      ...prev,
      colors: {
        ...prev.colors,
        [colorMode]: {
          ...prev.colors?.[colorMode],
          [colorKey]: value,
        },
      },
    }));
  };

  // Update typography
  const updateTypography = (key: string, value: string | number) => {
    setClientTheme((prev) => ({
      ...prev,
      typography: {
        ...prev.typography,
        [key]: value,
      },
    }));
  };

  // Export theme JSON
  const exportTheme = () => {
    const blob = new Blob([JSON.stringify(clientTheme, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${clientTheme.client.slug}-theme.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Sample data for preview
  const sampleTimeseriesData = [
    { date: '2024-01', value: 120 },
    { date: '2024-02', value: 150 },
    { date: '2024-03', value: 180 },
    { date: '2024-04', value: 160 },
    { date: '2024-05', value: 200 },
  ];

  const sampleCategoricalData = [
    { category: 'Product A', value: 250 },
    { category: 'Product B', value: 180 },
    { category: 'Product C', value: 320 },
    { category: 'Product D', value: 150 },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '8px', fontSize: '28px', fontWeight: 600 }}>
        Theme Studio
      </h1>
      <p style={{ marginBottom: '32px', color: 'var(--text-secondary)' }}>
        Create and customize client-specific themes while maintaining Kearney brand guidelines.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* Editor Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Client Selection */}
          <section
            style={{
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              padding: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>
              Client
            </h2>

            <div style={{ marginBottom: '16px' }}>
              <label
                htmlFor="client-select"
                style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
              >
                Load Existing
              </label>
              <select
                id="client-select"
                value={selectedClient}
                onChange={(e) => loadClientTheme(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--background)',
                  color: 'var(--text)',
                }}
              >
                <option value="">-- New Client --</option>
                {clients.map((slug) => (
                  <option key={slug} value={slug}>
                    {slug}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label
                htmlFor="client-slug"
                style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
              >
                Slug
              </label>
              <input
                id="client-slug"
                type="text"
                value={clientTheme.client.slug}
                onChange={(e) =>
                  setClientTheme((prev) => ({
                    ...prev,
                    client: { ...prev.client, slug: e.target.value.toLowerCase() },
                  }))
                }
                placeholder="acme-corp"
                pattern="[a-z0-9-]+"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--background)',
                  color: 'var(--text)',
                }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label
                htmlFor="client-name"
                style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}
              >
                Name
              </label>
              <input
                id="client-name"
                type="text"
                value={clientTheme.client.name}
                onChange={(e) =>
                  setClientTheme((prev) => ({
                    ...prev,
                    client: { ...prev.client, name: e.target.value },
                  }))
                }
                placeholder="ACME Corporation"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--background)',
                  color: 'var(--text)',
                }}
              />
            </div>
          </section>

          {/* Colors - Light Mode */}
          <section
            style={{
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              padding: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>
              Colors - Light Mode
            </h2>

            {['primary', 'emphasis', 'background', 'surface', 'text'].map((colorKey) => (
              <div key={colorKey} style={{ marginBottom: '12px' }}>
                <label
                  htmlFor={`light-${colorKey}`}
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: 500,
                    textTransform: 'capitalize',
                  }}
                >
                  {colorKey}
                </label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    id={`light-${colorKey}`}
                    type="color"
                    value={clientTheme.colors?.light?.[colorKey] || '#000000'}
                    onChange={(e) => updateColor('light', colorKey, e.target.value)}
                    style={{ width: '48px', height: '32px', cursor: 'pointer' }}
                  />
                  <input
                    type="text"
                    value={clientTheme.colors?.light?.[colorKey] || ''}
                    onChange={(e) => updateColor('light', colorKey, e.target.value)}
                    placeholder="#000000"
                    pattern="^#[0-9A-Fa-f]{6}$"
                    style={{
                      flex: 1,
                      padding: '6px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border)',
                      backgroundColor: 'var(--background)',
                      color: 'var(--text)',
                      fontFamily: 'monospace',
                    }}
                  />
                </div>
              </div>
            ))}
          </section>

          {/* Colors - Dark Mode */}
          <section
            style={{
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              padding: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>
              Colors - Dark Mode
            </h2>

            {['primary', 'emphasis', 'background', 'surface', 'text'].map((colorKey) => (
              <div key={colorKey} style={{ marginBottom: '12px' }}>
                <label
                  htmlFor={`dark-${colorKey}`}
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: 500,
                    textTransform: 'capitalize',
                  }}
                >
                  {colorKey}
                </label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    id={`dark-${colorKey}`}
                    type="color"
                    value={clientTheme.colors?.dark?.[colorKey] || '#FFFFFF'}
                    onChange={(e) => updateColor('dark', colorKey, e.target.value)}
                    style={{ width: '48px', height: '32px', cursor: 'pointer' }}
                  />
                  <input
                    type="text"
                    value={clientTheme.colors?.dark?.[colorKey] || ''}
                    onChange={(e) => updateColor('dark', colorKey, e.target.value)}
                    placeholder="#FFFFFF"
                    pattern="^#[0-9A-Fa-f]{6}$"
                    style={{
                      flex: 1,
                      padding: '6px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border)',
                      backgroundColor: 'var(--background)',
                      color: 'var(--text)',
                      fontFamily: 'monospace',
                    }}
                  />
                </div>
              </div>
            ))}
          </section>

          {/* Typography */}
          <section
            style={{
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              padding: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>
              Typography
            </h2>

            <div style={{ marginBottom: '12px' }}>
              <label
                htmlFor="font-family"
                style={{ display: 'block', marginBottom: '4px', fontWeight: 500 }}
              >
                Font Family
              </label>
              <input
                id="font-family"
                type="text"
                value={clientTheme.typography?.fontFamilyPrimary || ''}
                onChange={(e) => updateTypography('fontFamilyPrimary', e.target.value)}
                placeholder="Inter, Arial, sans-serif"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--background)',
                  color: 'var(--text)',
                }}
              />
              <small style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                Must include fallbacks (e.g., sans-serif)
              </small>
            </div>
          </section>

          {/* Actions */}
          <section style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button
              onClick={saveClientTheme}
              disabled={saveStatus === 'saving'}
              style={{
                padding: '12px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: 'var(--emphasis)',
                color: 'white',
                fontWeight: 600,
                cursor: saveStatus === 'saving' ? 'not-allowed' : 'pointer',
                opacity: saveStatus === 'saving' ? 0.6 : 1,
              }}
            >
              {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : 'Save Theme'}
            </button>

            <button
              onClick={validateTheme}
              style={{
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--surface)',
                color: 'var(--text)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Validate Theme
            </button>

            <button
              onClick={exportTheme}
              style={{
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--surface)',
                color: 'var(--text)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Export JSON
            </button>
          </section>
        </div>

        {/* Preview Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <section
            style={{
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              padding: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Live Preview</h2>
              <button
                onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                style={{
                  padding: '6px 12px',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--background)',
                  color: 'var(--text)',
                  cursor: 'pointer',
                }}
              >
                Toggle {theme === 'light' ? 'Dark' : 'Light'}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
              <KPICard
                title="Revenue"
                value="$2.4M"
                change="+12.5%"
                changeType="positive"
              />
              <KPICard
                title="Customers"
                value="1,234"
                change="+5.2%"
                changeType="positive"
              />
              <KPICard
                title="Churn Rate"
                value="2.8%"
                change="-0.5%"
                changeType="negative"
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
                Timeseries Chart
              </h3>
              <TimeseriesChart
                data={sampleTimeseriesData}
                xKey="date"
                yKey="value"
                height={200}
              />
            </div>

            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
                Categorical Bar Chart
              </h3>
              <CategoricalBarChart
                data={sampleCategoricalData}
                xKey="category"
                yKey="value"
                height={200}
              />
            </div>
          </section>

          {/* Constraints Info */}
          <section
            style={{
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              padding: '20px',
              border: '1px solid var(--border)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
              Kearney Design Constraints
            </h2>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'var(--text-secondary)' }}>
              <li style={{ marginBottom: '8px' }}>✓ No emojis allowed</li>
              <li style={{ marginBottom: '8px' }}>✓ No gridlines in charts</li>
              <li style={{ marginBottom: '8px' }}>✓ Labels before icons</li>
              <li style={{ marginBottom: '8px' }}>✓ Spot color for emphasis only</li>
              <li>✓ Font fallbacks required</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
