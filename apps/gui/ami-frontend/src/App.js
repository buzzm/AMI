import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
    const targURL = process.env.REACT_APP_TARG_URL || "http://localhost:5001"; // Configurable target URL

    const [input, setInput] = useState('');
    const [leftBoxContent, setLeftBoxContent] = useState('');
    const [vars, setVars] = useState([]);
    const [dataOutput, setDataOutput] = useState([]);
    const [stashPrompt, setStashPrompt] = useState(false);
    const [lastRmsg, setLastRmsg] = useState(null);
    const [systemSize, setSystemSize] = useState('simple'); // New state for system size
    const [loading, setLoading] = useState(false); // New state for loading spinner
    const [introContent, setIntroContent] = useState('');  // To store /intro content

    const leftBoxRef = useRef(null);

    useEffect(() => {
        const fetchIntroContent = async () => {
            try {
                const response = await fetch(targURL + '/intro', {
                    method: 'GET',
                    headers: { 'Content-Type': 'text/html' },
                    credentials: 'include'
                });
                const htmlContent = await response.text();
                setIntroContent(htmlContent);  // Set the intro content in the state
            } catch (error) {
                setIntroContent('<p>Hello!  The AMI Server is undergoing maintenance or an upgrade now; try again soon!</p>');
            }
        };

        fetchIntroContent();
    }, [targURL]);

    useEffect(() => {
        // Auto scroll to bottom when content changes
        if (leftBoxRef.current) {
            leftBoxRef.current.scrollTop = leftBoxRef.current.scrollHeight;
        }
    }, [leftBoxContent]);

    const handleSubmit = async () => {
        setLoading(true); // Activate the loading spinner
        const sizeCode = systemSize;  // Fetch selected system size value
        setLeftBoxContent(prev => `${prev}\n\n<span class="user-input">${input}</span>\n\n`);
        try {
            const response = await fetch(targURL + '/sparql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: input, systemSize: sizeCode }),  // Pass selected system size
                credentials: 'include'
            });
            const data = await response.json();
            processResponse(data);
            setLastRmsg(data);
        } catch (error) {
	    setLeftBoxContent(prev => `${prev}\n<span class="response blue-text">Error retrieving data: ${error.message}</span>`);
            console.error('Error details:', error);  // Log the full error for debugging
   
            // setLeftBoxContent(prev => `${prev}\n<span class="response blue-text">Error retrieving data.</span>`);
        } finally {
            setLoading(false); // Deactivate the loading spinner
        }
    };


    const processResponse = (rmsg) => {
	let narrative = rmsg.narrative;

	// Always reset to false because narrative AFTER SPARQL will
	// get picked up and is not what screen actually reflects...
        setStashPrompt(false);
	
	// Check if the narrative starts with "## SPARQL"
	if (!narrative.startsWith("## SPARQL")) {
            // Split the narrative by existing newlines first
            let lines = narrative.split("\n");
            let formattedNarrative = "";

            lines.forEach(line => {
		let words = line.split(" ");
		let newLine = "";
		let lineLength = 0;

		words.forEach(word => {
                    if (lineLength + word.length + 1 > 100) {
			// If the current line length + the new word exceeds 100 chars, start a new line
			formattedNarrative += newLine.trim() + "\n";  // Add the current line to the narrative
			newLine = "";  // Reset for the next line
			lineLength = 0;
                    }

                    newLine += word + " ";  // Add the word to the current line
                    lineLength += word.length + 1;  // Update the line length
		});

		// Add any remaining words in the line
		formattedNarrative += newLine.trim() + "\n";
            });

            narrative = formattedNarrative.trim(); // Clean up extra whitespace or newlines
	}

	// Append the formatted narrative to the left box content
	setLeftBoxContent(prev => `${prev}\n<span class="response blue-text">${narrative}</span>`);
	
	if (rmsg.vars.length > 0) {
            setVars(rmsg.vars);
            setDataOutput(rmsg.data.length > 0 ? rmsg.data : []);
            setStashPrompt(true);
	}
    };


    const handleSystemSizeChange = (e) => {
        const newSize = e.target.value;
        setSystemSize(newSize);
        setLeftBoxContent(prev => `${prev}\n<span class="response blue-text">Switching to domain ${newSize.charAt(0).toUpperCase() + newSize.slice(1)}.</span>`);
    };

    const handleStashResponse = async (answer) => {
        if (answer === 'yes' && lastRmsg) {
            try {
                const stashResponse = await fetch(targURL + '/stash', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(lastRmsg),
                    credentials: 'include'
                });
                const rmsg2 = await stashResponse.json();
                setLeftBoxContent(prev => `${prev}\n<span class="response blue-text">${rmsg2.narrative}</span>`);
            } catch (error) {
                setLeftBoxContent(prev => `${prev}\n<span class="response blue-text">Error stashing data.</span>`);
            }
        }
        setStashPrompt(false);
    };

    const renderTable = () => (
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

    return (
        <div className="App">
            <div className="header-area">
                <div className="title">AMI: Asset Management & Intelligence</div>
                <div className="system-size-dropdown">
                    <label htmlFor="system-size">System Size:</label>
                    <select
                        id="system-size"
                        value={systemSize}
                        onChange={handleSystemSizeChange} // Updated event handler
                    >
                        <option value="simple">Hello World</option>
                        <option value="standard">Standard</option>
                    </select>
                </div>
                <div className="links">
                    <a href="/help.html" target="_blank">Help</a>
                    <a href="/contact.html" target="_blank">Contact</a>
                </div>
            </div>
            <div className="main-container">
                <div className="left-side">
		    
                    <div className="left-box" ref={leftBoxRef}>
			<div dangerouslySetInnerHTML={{ __html: introContent }} className="intro-content" />			
                        <pre dangerouslySetInnerHTML={{ __html: leftBoxContent }}></pre>
                    </div>
		    
                    <div className="input-container">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder='Enter your query e.g. "Show all AMI software."'
                            className="input-box"
                        />
                        <button onClick={handleSubmit} className="go-button" disabled={loading}>
                            {loading ? <span className="spinner"></span> : 'GO'} {/* Spinner */}
                        </button>
                    </div>
                </div>
                <div className="right-side">
                    <div className="right-box">
                        {renderTable()}
                    </div>
                    <div className="actions-area">
                        {stashPrompt && (
                            <>
                                <p>Do you want to stash the data?</p>
                                <button onClick={() => handleStashResponse('yes')}>Yes</button>
                                <button onClick={() => handleStashResponse('no')}>No</button>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
