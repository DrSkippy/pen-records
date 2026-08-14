import React from 'react'
import ReactDOM from 'react-dom/client'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {CssBaseline,ThemeProvider,createTheme} from '@mui/material'
import App from './App'
import './styles.css'

const theme=createTheme({palette:{mode:'light',primary:{main:'#60452f'},secondary:{main:'#20766c'},background:{default:'#f5f1e9',paper:'#fffdf8'}},shape:{borderRadius:14},typography:{fontFamily:'Inter,system-ui,sans-serif',h1:{fontFamily:'Georgia,serif'},h2:{fontFamily:'Georgia,serif'}}})
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={new QueryClient()}><ThemeProvider theme={theme}><CssBaseline/><App/></ThemeProvider></QueryClientProvider></React.StrictMode>)
