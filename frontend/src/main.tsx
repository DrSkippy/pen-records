import React from 'react'
import ReactDOM from 'react-dom/client'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {CssBaseline,ThemeProvider,createTheme} from '@mui/material'
import App from './App'
import './styles.css'

const theme=createTheme({palette:{mode:'light',primary:{main:'#6E1F2E',contrastText:'#F7F4ED'},secondary:{main:'#3E8C8C',contrastText:'#F7F4ED'},background:{default:'#F7F4ED',paper:'#F7F4ED'},text:{primary:'#2C2C2A',secondary:'#59616A'},divider:'#A9ADB2',error:{main:'#9A2438'}},shape:{borderRadius:12},typography:{fontFamily:'Inter,system-ui,sans-serif',h1:{fontFamily:'Georgia,serif',color:'#1E2A44'},h2:{fontFamily:'Georgia,serif',color:'#1E2A44'},h3:{fontFamily:'Georgia,serif',color:'#1E2A44'},h4:{fontFamily:'Georgia,serif',color:'#1E2A44'},h5:{fontFamily:'Georgia,serif',color:'#1E2A44'},h6:{color:'#1E2A44'}},components:{MuiAppBar:{styleOverrides:{root:{backgroundColor:'#1E2A44'}}},MuiCard:{styleOverrides:{root:{borderColor:'#A9ADB2'}}},MuiTabs:{styleOverrides:{indicator:{backgroundColor:'#6E1F2E'}}},MuiTab:{styleOverrides:{root:{'&.Mui-selected':{color:'#1E2A44'}}}},MuiBottomNavigation:{styleOverrides:{root:{backgroundColor:'#F7F4ED',borderTop:'1px solid #A9ADB2'}}},MuiBottomNavigationAction:{styleOverrides:{root:{'&.Mui-selected':{color:'#6E1F2E'}}}}}})
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={new QueryClient()}><ThemeProvider theme={theme}><CssBaseline/><App/></ThemeProvider></QueryClientProvider></React.StrictMode>)
