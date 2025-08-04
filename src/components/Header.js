import React from 'react';

function Header({ interfaces, selectedInterface, setSelectedInterface }) {
  return (
    <div className="top-header">
      <div className="header-left">
        <h1>VABiKo Demo Application</h1>
        <p>Explore various features and interfaces for the VABiKo image archive</p>
      </div>
      
      <div className="interface-selector">
        <label htmlFor="interface-select">
          <strong>Select Interface:</strong>
        </label>
        <select
          id="interface-select"
          value={selectedInterface}
          onChange={(e) => setSelectedInterface(e.target.value)}
        >
          <option value="">Choose an interface...</option>
          {interfaces.map((iface) => (
            <option key={iface.id} value={iface.id}>
              {iface.name} - {iface.description}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default Header;