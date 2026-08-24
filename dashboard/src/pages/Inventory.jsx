import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { fetchInventory } from '../api';

const DEMO_ITEMS = [
  { id: 'item-001', name: 'Basmati Rice 5kg', category: 'dry-goods', zone: 'dry-storage', shelfId: 'shelf-01', currentWeight: 18.0, fullWeight: 25.0, reorderPoint: 5.0, unit: 'kg', stockPercentage: 0.72, stockLevel: 'ADEQUATE', depletionRate: 0.12, estimatedHoursRemaining: 150, needsReorder: false },
  { id: 'item-002', name: 'All-Purpose Flour 2kg', category: 'dry-goods', zone: 'dry-storage', shelfId: 'shelf-02', currentWeight: 9.0, fullWeight: 20.0, reorderPoint: 4.0, unit: 'kg', stockPercentage: 0.45, stockLevel: 'ADEQUATE', depletionRate: 0.08, estimatedHoursRemaining: 112.5, needsReorder: false },
  { id: 'item-003', name: 'Granulated Sugar 1kg', category: 'dry-goods', zone: 'dry-storage', shelfId: 'shelf-03', currentWeight: 13.2, fullWeight: 15.0, reorderPoint: 3.0, unit: 'kg', stockPercentage: 0.88, stockLevel: 'FULL', depletionRate: 0.05, estimatedHoursRemaining: 264, needsReorder: false },
  { id: 'item-004', name: 'Whole Milk 1L', category: 'dairy', zone: 'refrigerated', shelfId: 'shelf-04', currentWeight: 2.16, fullWeight: 12.0, reorderPoint: 3.0, unit: 'kg', stockPercentage: 0.18, stockLevel: 'CRITICAL', depletionRate: 0.25, estimatedHoursRemaining: 8.64, needsReorder: true },
  { id: 'item-005', name: 'Cheddar Cheese Block', category: 'dairy', zone: 'refrigerated', shelfId: 'shelf-05', currentWeight: 4.96, fullWeight: 8.0, reorderPoint: 2.0, unit: 'kg', stockPercentage: 0.62, stockLevel: 'ADEQUATE', depletionRate: 0.06, estimatedHoursRemaining: 82.7, needsReorder: false },
  { id: 'item-006', name: 'Fresh Chicken Breast', category: 'meat', zone: 'refrigerated', shelfId: 'shelf-06', currentWeight: 3.3, fullWeight: 10.0, reorderPoint: 2.5, unit: 'kg', stockPercentage: 0.33, stockLevel: 'LOW', depletionRate: 0.18, estimatedHoursRemaining: 18.3, needsReorder: false },
  { id: 'item-007', name: 'Frozen Mixed Vegetables', category: 'frozen', zone: 'frozen', shelfId: 'shelf-07', currentWeight: 16.38, fullWeight: 18.0, reorderPoint: 3.5, unit: 'kg', stockPercentage: 0.91, stockLevel: 'FULL', depletionRate: 0.04, estimatedHoursRemaining: 409.5, needsReorder: false },
  { id: 'item-008', name: 'Ice Cream Tubs 500ml', category: 'frozen', zone: 'frozen', shelfId: 'shelf-08', currentWeight: 7.7, fullWeight: 14.0, reorderPoint: 3.0, unit: 'kg', stockPercentage: 0.55, stockLevel: 'ADEQUATE', depletionRate: 0.07, estimatedHoursRemaining: 110, needsReorder: false },
  { id: 'item-009', name: 'Olive Oil 500ml Bottles', category: 'condiments', zone: 'dry-storage', shelfId: 'shelf-09', currentWeight: 9.36, fullWeight: 12.0, reorderPoint: 2.5, unit: 'kg', stockPercentage: 0.78, stockLevel: 'ADEQUATE', depletionRate: 0.03, estimatedHoursRemaining: 312, needsReorder: false },
  { id: 'item-010', name: 'Fresh Orange Juice 1L', category: 'beverages', zone: 'refrigerated', shelfId: 'shelf-10', currentWeight: 1.92, fullWeight: 16.0, reorderPoint: 4.0, unit: 'kg', stockPercentage: 0.12, stockLevel: 'CRITICAL', depletionRate: 0.20, estimatedHoursRemaining: 9.6, needsReorder: true },
  { id: 'item-011', name: 'Canned Tomatoes 400g', category: 'canned', zone: 'dry-storage', shelfId: 'shelf-11', currentWeight: 13.4, fullWeight: 20.0, reorderPoint: 4.0, unit: 'kg', stockPercentage: 0.67, stockLevel: 'ADEQUATE', depletionRate: 0.06, estimatedHoursRemaining: 223.3, needsReorder: false },
  { id: 'item-012', name: 'Penne Pasta 500g', category: 'dry-goods', zone: 'dry-storage', shelfId: 'shelf-12', currentWeight: 7.38, fullWeight: 18.0, reorderPoint: 3.5, unit: 'kg', stockPercentage: 0.41, stockLevel: 'ADEQUATE', depletionRate: 0.09, estimatedHoursRemaining: 82, needsReorder: false },
];

const CATEGORIES = ['All', 'dry-goods', 'dairy', 'meat', 'frozen', 'condiments', 'beverages', 'canned'];

export default function Inventory() {
  const [items, setItems] = useState(DEMO_ITEMS);
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [sortField, setSortField] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  useEffect(() => {
    fetchInventory()
      .then(setItems)
      .catch(() => console.log('Using demo inventory data'));
  }, []);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const filtered = useMemo(() => {
    let result = items;
    if (filter !== 'All') result = result.filter(i => i.category === filter);
    if (search) result = result.filter(i =>
      i.name.toLowerCase().includes(search.toLowerCase()) ||
      i.id.toLowerCase().includes(search.toLowerCase())
    );
    result = [...result].sort((a, b) => {
      let va = a[sortField], vb = b[sortField];
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return result;
  }, [items, filter, search, sortField, sortDir]);

  const formatHours = (h) => {
    if (h > 999) return '∞';
    if (h > 24) return `${Math.round(h / 24)}d`;
    return `${Math.round(h)}h`;
  };

  return (
    <>
      <div className="page-header">
        <h2>Inventory Management</h2>
        <p>Track stock levels, depletion rates, and reorder status across all shelves</p>
      </div>

      <div className="filter-bar">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            className={`filter-btn ${filter === cat ? 'active' : ''}`}
            onClick={() => setFilter(cat)}
          >
            {cat === 'All' ? 'All' : cat.replace('-', ' ')}
          </button>
        ))}
        <input
          className="search-input"
          placeholder="Search items..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="glass-card">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('name')}>Product {sortField === 'name' ? (sortDir === 'asc' ? '↑' : '↓') : ''}</th>
                <th onClick={() => handleSort('category')}>Category</th>
                <th onClick={() => handleSort('shelfId')}>Shelf</th>
                <th onClick={() => handleSort('currentWeight')}>Weight</th>
                <th onClick={() => handleSort('stockPercentage')}>Stock Level</th>
                <th onClick={() => handleSort('depletionRate')}>Depletion</th>
                <th onClick={() => handleSort('estimatedHoursRemaining')}>Time Left</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(item => (
                <tr key={item.id}>
                  <td>
                    <Link to={`/inventory/${item.id}`} style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                      {item.name}
                    </Link>
                  </td>
                  <td>{item.category}</td>
                  <td>{item.shelfId}</td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {item.currentWeight?.toFixed(1)} / {item.fullWeight} {item.unit}
                  </td>
                  <td>
                    <span className={`badge ${(item.stockLevel || 'adequate').toLowerCase()}`}>
                      {Math.round((item.stockPercentage || 0) * 100)}%
                    </span>
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {item.depletionRate?.toFixed(2)} kg/h
                  </td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {formatHours(item.estimatedHoursRemaining || Infinity)}
                  </td>
                  <td>
                    {item.needsReorder ? (
                      <span className="badge critical">REORDER</span>
                    ) : (
                      <span style={{ color: 'var(--accent-emerald)', fontSize: '0.8rem' }}>OK</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
