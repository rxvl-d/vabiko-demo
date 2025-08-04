import React from 'react';

function Header({ interfaces, selectedInterface, setSelectedInterface }) {
  return (
    <div className="flex flex-col md:flex-row gap-5 mb-8 p-5 bg-white rounded-lg shadow-sm">
      <div className="flex-1 md:max-w-[50%]">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">VABiKo Demo Application</h1>
        <p className="text-gray-600 text-sm">Explore various features and interfaces for the VABiKo image archive</p>
      </div>
      
      <div className="flex-1 md:max-w-[50%] flex flex-col md:items-end">
        <label htmlFor="interface-select" className="font-semibold mb-2 md:text-right">
          Select Interface:
        </label>
        <select
          id="interface-select"
          value={selectedInterface}
          onChange={(e) => setSelectedInterface(e.target.value)}
          className="w-full md:max-w-md px-3 py-2 border border-gray-300 rounded-md bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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