import React, { useState } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');       // User input
  const [narrative, setNarrative] = useState(''); // Narrative output
  const [sparql, setSparql] = useState('');     // SPARQL output
  const [vars, setVars] = useState([]);         // Column headers for the data table
  const [dataOutput, setDataOutput] = useState([]); // Data rows for the data table
  const [stashPrompt, setStashPrompt] = useState(false); // Prompt for stashing
  const [lastRmsg, setLastRmsg] = useState(null); // Last response message for stashing

  const handleSubmit = async () => {
    try {
      const response = await fetch('http://localhost:5001/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input, systemSize: 'Simple' }),  // Example body
        credentials: 'include'  // Allow sending cookies
      });

      const data = await response.json();
      processResponse(data);  // Process the response
      setLastRmsg(data);      // Save the last rmsg for stashing later

    } catch (error) {
      console.error("Error fetching data:", error);
      setNarrative("Error retrieving data.");
    }
  };

  // Process the server response
  const processResponse = (rmsg) => {
    if (rmsg.vars.length === 0) {
      // No SPARQL generated; only narrative
      setNarrative(rmsg.narrative);
      setSparql('');  // Clear SPARQL box
      setVars([]);  // Clear table headers
      setDataOutput([]);  // Clear Data rows
    } else {
      // SPARQL was generated
      setSparql(rmsg.narrative); // SPARQL comes back in narrative
      setNarrative('');  // Clear Narrative box

      // Set headers (vars) and rows (data) for the table
      setVars(rmsg.vars);  // Headers for the table

      if (rmsg.data.length > 0) {
        setDataOutput(rmsg.data);  // Rows of data for the table
      } else {
        setDataOutput([]);  // No data, but display headers
      }

      setStashPrompt(true);  // Prompt for stashing
    }
  };

  // Handle stashing of data
  const handleStashResponse = async (answer) => {
    if (answer === 'yes' && lastRmsg) {
      try {
        const stashResponse = await fetch('http://localhost:5001/stash', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(lastRmsg),  // Send the last rmsg
          credentials: 'include'  // Allow sending cookies
        });

        const rmsg2 = await stashResponse.json();
        setNarrative(rmsg2.narrative);  // Show new narrative from stash response
      } catch (error) {
        console.error("Error stashing data:", error);
        setNarrative("Error stashing data.");
      }
    }

    // Either way, hide stash prompt
    setStashPrompt(false);
  };

  // Render the dynamic table
  const renderTable = () => {
    return (
      <table className="data-table">
        <thead>
          <tr>
            {vars.map((header, index) => (
              <th key={index}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataOutput.length > 0 ? (
            dataOutput.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {vars.map((header, colIndex) => (
                  <td key={colIndex}>{row[header]}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={vars.length}>No data available</td>
            </tr>
          )}
        </tbody>
      </table>
    );
  };

  return (
    <div className="App">
      <h1>AMI Query System</h1>

      <div className="input-box">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your query"
        />
        <button onClick={handleSubmit}>Submit</button>
      </div>

      <div className="output-section">
        <div className="narrative-box">
          <h3>Narrative Output</h3>
          <pre>{narrative}</pre>
        </div>

        <div className="sparql-box">
          <h3>SPARQL Output</h3>
          <pre>{sparql}</pre>
        </div>
      </div>
	
      <div className="data-box">
        <h3>Data Output</h3>
        {renderTable()}  {/* Render the dynamic table */}
      </div>


      {stashPrompt && (
        <div className="stash-prompt">
          <p>Do you want to stash the data?</p>
          <button onClick={() => handleStashResponse('yes')}>Yes</button>
          <button onClick={() => handleStashResponse('no')}>No</button>
        </div>
      )}
    </div>
  );
}

export default App;

