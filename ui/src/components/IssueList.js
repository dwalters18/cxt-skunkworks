// ui/src/components/IssueList.js

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const IssueList = () => {
    const [issues, setIssues] = useState([]);
    const [selectedIssue, setSelectedIssue] = useState(null);
    const [summary, setSummary] = useState('');

    useEffect(() => {
        fetchIssues();
    }, []);

    const fetchIssues = async () => {
        try {
            const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/issues`);
            setIssues(response.data);
        } catch (error) {
            console.error('Error fetching issues:', error);
        }
    };

    const getSummary = async (issue) => {
        try {
            const response = await axios.post(
                `${process.env.REACT_APP_BACKEND_URL}/api/summarize`,
                { text: issue.description }
            );
            setSummary(response.data.summary);
            setSelectedIssue(issue);
        } catch (error) {
            console.error('Error getting summary:', error);
        }
    };

    return (
        <div>
            <h1>JIRA Issues</h1>
            <ul>
                {issues.map((issue) => (
                    <li key={issue.key}>
                        <h3>{issue.title}</h3>
                        <button onClick={() => getSummary(issue)}>Get Summary</button>
                    </li>
                ))}
            </ul>

            {selectedIssue && summary && (
                <div>
                    <h2>Summary for {selectedIssue.title}:</h2>
                    <p>{summary}</p>
                </div>
            )}
        </div>
    );
};

export default IssueList;
