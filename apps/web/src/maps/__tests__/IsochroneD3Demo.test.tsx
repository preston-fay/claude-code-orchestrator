import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { IsochroneD3Demo } from '../IsochroneD3Demo';
import { ThemeProvider } from '../../contexts/ThemeContext';
import { BrowserRouter } from 'react-router-dom';

// Mock Leaflet components
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
}));

// Mock LeafletD3Overlay
vi.mock('../LeafletD3Overlay', () => ({
  LeafletD3Overlay: () => <div data-testid="d3-overlay">Overlay</div>,
}));

const renderDemo = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <IsochroneD3Demo />
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('IsochroneD3Demo', () => {
  it('renders with title and description', () => {
    renderDemo();

    expect(screen.getByText('Isochrone Map with D3 Overlay')).toBeTruthy();
    expect(
      screen.getByText(/Brand-compliant isochrone visualization/)
    ).toBeTruthy();
  });

  it('renders all control elements', () => {
    renderDemo();

    expect(screen.getByText('Provider:')).toBeTruthy();
    expect(screen.getByText('Profile:')).toBeTruthy();
    expect(screen.getByText(/Range:/)).toBeTruthy();
    expect(screen.getByText(/Buckets:/)).toBeTruthy();
  });

  it('renders provider select with all options', () => {
    renderDemo();

    const select = screen.getByDisplayValue('Stub (Demo)');
    expect(select).toBeTruthy();

    const options = (select as HTMLSelectElement).options;
    expect(options.length).toBe(3);
    expect(options[0].value).toBe('stub');
    expect(options[1].value).toBe('openrouteservice');
    expect(options[2].value).toBe('mapbox');
  });

  it('renders profile select with all options', () => {
    renderDemo();

    const select = screen.getByDisplayValue('Driving');
    expect(select).toBeTruthy();

    const options = (select as HTMLSelectElement).options;
    expect(options.length).toBe(3);
    expect(options[0].value).toBe('driving');
    expect(options[1].value).toBe('walking');
    expect(options[2].value).toBe('cycling');
  });

  it('updates range value when slider changes', async () => {
    renderDemo();

    const rangeInput = screen.getByRole('slider', { name: /Range/ });
    expect(rangeInput).toBeTruthy();

    fireEvent.change(rangeInput, { target: { value: '45' } });

    await waitFor(() => {
      expect(screen.getByText(/Range: 45 min/)).toBeTruthy();
    });
  });

  it('updates buckets value when slider changes', async () => {
    renderDemo();

    const bucketInput = screen.getByRole('slider', { name: /Buckets/ });
    expect(bucketInput).toBeTruthy();

    fireEvent.change(bucketInput, { target: { value: '4' } });

    await waitFor(() => {
      expect(screen.getByText(/Buckets: 4/)).toBeTruthy();
    });
  });

  it('changes provider when select changes', async () => {
    renderDemo();

    const providerSelect = screen.getByDisplayValue('Stub (Demo)');
    fireEvent.change(providerSelect, { target: { value: 'openrouteservice' } });

    await waitFor(() => {
      expect((providerSelect as HTMLSelectElement).value).toBe('openrouteservice');
    });
  });

  it('changes profile when select changes', async () => {
    renderDemo();

    const profileSelect = screen.getByDisplayValue('Driving');
    fireEvent.change(profileSelect, { target: { value: 'walking' } });

    await waitFor(() => {
      expect((profileSelect as HTMLSelectElement).value).toBe('walking');
    });
  });

  it('renders legend with correct number of buckets', async () => {
    renderDemo();

    const bucketInput = screen.getByRole('slider', { name: /Buckets/ });
    fireEvent.change(bucketInput, { target: { value: '4' } });

    await waitFor(() => {
      const legend = screen.getByText('Legend:').parentElement;
      const legendItems = legend?.querySelectorAll('div[style*="opacity"]');
      expect(legendItems?.length).toBe(4);
    });
  });

  it('renders map container and tile layer', () => {
    renderDemo();

    expect(screen.getByTestId('map-container')).toBeTruthy();
    expect(screen.getByTestId('tile-layer')).toBeTruthy();
  });

  it('renders D3 overlay component', () => {
    renderDemo();

    expect(screen.getByTestId('d3-overlay')).toBeTruthy();
  });

  it('displays brand compliance footer', () => {
    renderDemo();

    expect(
      screen.getByText(/No gridlines • Label-first • Spot color emphasis/)
    ).toBeTruthy();
  });

  it('verifies no emojis in rendered output', () => {
    const { container } = renderDemo();
    const text = container.textContent || '';

    // Check for common emoji patterns
    const emojiRegex = /[\u{1F600}-\u{1F64F}]/u;
    expect(emojiRegex.test(text)).toBe(false);
  });
});
