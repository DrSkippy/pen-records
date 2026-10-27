import {Box,Card,CardActionArea,CardContent,Chip,Stack,Typography} from '@mui/material'
import {FountainPenIcon} from './icons'
import {FramedPhoto} from './FramedPhoto'
import type {Nib,Pen} from './types'

const prettyDate=(value:string|null)=>value?new Date(`${value}T12:00:00`).toLocaleDateString():''
export const materialChipSx=(material:string)=>{
  const name=material.toLowerCase()
  if(name.includes("gold"))return {bgcolor:"#F2D98A",color:"#3A2C00","&:hover":{bgcolor:"#E8CC74"}}
  if(name.includes("stainless")||name.includes("steel"))return {bgcolor:"#DDE2E7",color:"#1F2433","&:hover":{bgcolor:"#CDD3D9"}}
  if(name.includes("titanium"))return {bgcolor:"#8B949C",color:"#1F2433","&:hover":{bgcolor:"#7A838B"}}
  return undefined
}
export const nibSpec=(nib:Nib)=>[nib.line_width,nib.nib_size,nib.material.name].filter(Boolean).join(' · ')
export function NibChip({nib}:{nib:Nib|undefined}){return <Chip size="small" label={nib?nibSpec(nib):'Unknown nib'} sx={materialChipSx(nib?.material.name||'')}/>}

export function PenCard({pen,onOpen}:{pen:Pen;onOpen:()=>void}){
  const installation=pen.installations.find(item=>item.is_current)
  const nib=pen.nibs.find(item=>item.id===installation?.nib_id)??pen.nibs.find(item=>item.is_original)
  const image=pen.images[0]
  return <Card className="pen-card" variant="outlined"><CardActionArea onClick={onOpen} className="pen-card-action">
    {image?<FramedPhoto key={image.id} className="pen-card-photo" src={image.thumbnail_url} alt={image.caption||`${pen.maker.name} ${pen.model}`} ratio={16/6}/>:<Box className="pen-card-image pen-image-placeholder"><FountainPenIcon fontSize="large"/></Box>}
    <CardContent className="pen-card-content"><Typography className="pen-card-maker" variant="overline" component="p">{pen.maker.name}</Typography><Typography className="pen-card-model" variant="h6" component="h2">{pen.model}</Typography><Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" alignItems="center" sx={{mt:1.25}}><NibChip nib={nib}/>{nib?.description&&<Typography variant="body2" color="text.secondary">{nib.description}</Typography>}{pen.disposed_on&&<Chip size="small" variant="outlined" label={`Disposed ${prettyDate(pen.disposed_on)}`}/>}</Stack></CardContent>
  </CardActionArea></Card>
}
