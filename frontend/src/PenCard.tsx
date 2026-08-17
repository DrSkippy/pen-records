import {MenuBook} from '@mui/icons-material'
import {Box,Card,CardActionArea,CardContent,Chip,Stack,Typography} from '@mui/material'
import type {Pen} from './types'

const prettyDate=(value:string|null)=>value?new Date(`${value}T12:00:00`).toLocaleDateString():''
const materialChipSx=(material:string)=>{
  const name=material.toLowerCase()
  if(name.includes("gold"))return {bgcolor:"#d4af37",color:"#241a00","&:hover":{bgcolor:"#c5a12f"}}
  if(name.includes("stainless")||name.includes("steel"))return {bgcolor:"#c4c9ce",color:"#202428","&:hover":{bgcolor:"#b5bbc1"}}
  if(name.includes("titanium"))return {bgcolor:"#747b82",color:"#fff","&:hover":{bgcolor:"#666d73"}}
  return undefined
}

export function PenCard({pen,onOpen}:{pen:Pen;onOpen:()=>void}){
  const installation=pen.installations.find(item=>item.is_current)
  const nib=pen.nibs.find(item=>item.id===installation?.nib_id)??pen.nibs.find(item=>item.is_original)
  const image=pen.images[0]
  return <Card className="pen-card" variant="outlined"><CardActionArea onClick={onOpen} className="pen-card-action">
    {image?<img className="pen-card-image" src={image.thumbnail_url} alt={image.caption||`${pen.maker.name} ${pen.model}`}/>:<Box className="pen-image-placeholder"><MenuBook fontSize="large"/></Box>}
    <CardContent className="pen-card-content"><Typography className="pen-card-maker" variant="h5">{pen.maker.name}</Typography><Typography className="pen-card-model" variant="h6">{pen.model}</Typography><Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" alignItems="center" sx={{mt:1}}>{nib?.description&&<Typography color="text.secondary">{nib.description}</Typography>}{nib?.line_width&&<Chip size="small" label={nib.line_width}/>}{nib?.nib_size&&<Chip size="small" variant="outlined" label={nib.nib_size}/>}<Chip size="small" label={nib?.material.name||'Unknown nib'} sx={materialChipSx(nib?.material.name||'')}/>{pen.disposed_on&&<Chip size="small" label={`Disposed ${prettyDate(pen.disposed_on)}`}/>}</Stack></CardContent>
  </CardActionArea></Card>
}
