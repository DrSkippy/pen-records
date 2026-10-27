import {useState} from 'react'
import {ChevronLeft,ChevronRight,Close} from '@mui/icons-material'
import {Box,Dialog,IconButton,Typography} from '@mui/material'
import type {PenImage} from './types'

// Full-size, uncropped view of a pen's photos with arrow-key and button navigation
export function PhotoViewer({images,start,title,onClose}:{images:PenImage[];start:number;title:string;onClose:()=>void}){
  const [index,setIndex]=useState(start),image=images[index],many=images.length>1
  const step=(by:number)=>setIndex(current=>(current+by+images.length)%images.length)
  return <Dialog open onClose={onClose} maxWidth={false} aria-label={`${title} photos`} onKeyDown={e=>{if(many&&e.key==='ArrowLeft')step(-1);if(many&&e.key==='ArrowRight')step(1)}} slotProps={{paper:{className:'photo-viewer'}}}>
    <img className="photo-viewer-image" src={image.url} alt={image.caption||`${title} image ${index+1}`}/>
    <Box className="photo-viewer-bar"><Typography variant="body2">{image.caption||title}{many&&<Typography component="span" variant="body2" className="photo-viewer-count"> {index+1} / {images.length}</Typography>}</Typography>
      <Box>{many&&<><IconButton aria-label="Previous photo" onClick={()=>step(-1)}><ChevronLeft/></IconButton><IconButton aria-label="Next photo" onClick={()=>step(1)}><ChevronRight/></IconButton></>}<IconButton aria-label="Close" onClick={onClose}><Close/></IconButton></Box></Box>
  </Dialog>
}
