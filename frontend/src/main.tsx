import React from 'react'
import ReactDOM from 'react-dom/client'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {CssBaseline,ThemeProvider,createTheme} from '@mui/material'
import App from './App'
import './styles.css'

// Paper & Ink palette
const paper='#FAF7F2',card='#FFFFFF',ink='#1F2433',muted='#6B7280',hairline='#E7E1D7',blueBlack='#2E4A7D',copper='#D9653B',teal='#2A8C82',oxblood='#8E2C3F'
const serif='Georgia,serif'
const theme=createTheme({palette:{mode:'light',primary:{main:blueBlack,contrastText:'#FFFFFF'},secondary:{main:copper,contrastText:'#FFFFFF'},success:{main:teal,contrastText:'#FFFFFF'},error:{main:oxblood},background:{default:paper,paper:card},text:{primary:ink,secondary:muted},divider:hairline},shape:{borderRadius:12},typography:{fontFamily:'Inter,system-ui,sans-serif',h1:{fontFamily:serif},h2:{fontFamily:serif},h3:{fontFamily:serif},h4:{fontFamily:serif},h5:{fontFamily:serif},overline:{color:muted,fontWeight:600,letterSpacing:'.08em'}},components:{MuiAppBar:{styleOverrides:{root:{backgroundColor:card,color:ink,borderBottom:`1px solid ${hairline}`}}},MuiCard:{styleOverrides:{root:{borderColor:hairline}}},MuiTab:{styleOverrides:{root:{'&.Mui-selected':{color:blueBlack}}}},MuiBottomNavigation:{styleOverrides:{root:{backgroundColor:card,borderTop:`1px solid ${hairline}`}}},MuiBottomNavigationAction:{styleOverrides:{root:{'&.Mui-selected':{color:blueBlack}}}}}})
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={new QueryClient()}><ThemeProvider theme={theme}><CssBaseline/><App/></ThemeProvider></QueryClientProvider></React.StrictMode>)
