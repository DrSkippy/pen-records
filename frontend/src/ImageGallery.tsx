import {useState} from 'react'
import {Close} from '@mui/icons-material'
import {Alert,Box,Button,Card,CardContent,Dialog,DialogActions,DialogContent,DialogTitle,Grid,IconButton,Typography} from '@mui/material'
import {api} from './api'
import {FramedPhoto} from './FramedPhoto'
import {PhotoViewer} from './PhotoViewer'
import type {PenImage} from './types'

export function ImageGallery({penId,penModel,images,onDeleted}:{penId:string;penModel:string;images:PenImage[];onDeleted:()=>void}){
  const [selected,setSelected]=useState<PenImage|null>(null),[viewing,setViewing]=useState<number|null>(null),[deleting,setDeleting]=useState(false),[error,setError]=useState('')
  async function remove(){if(!selected)return;setDeleting(true);setError('');try{await api.deleteImage(penId,selected.id);setSelected(null);onDeleted()}catch(e){setError(e instanceof Error?e.message:'Unable to remove image')}finally{setDeleting(false)}}
  return <>{error&&<Alert severity="error" sx={{mb:2}}>{error}</Alert>}<Grid container spacing={2}>{images.map((image,index)=><Grid key={image.id} size={{xs:12,sm:6,md:4}}><Card variant="outlined" className="gallery-card"><Box className="gallery-image-wrap"><FramedPhoto key={image.id} src={image.url} sampleSrc={image.thumbnail_url} alt={image.caption||`${penModel} image ${index+1}`} ratio={16/6} minRatio={4/3} onOpen={()=>setViewing(index)}/><IconButton className="image-delete" size="small" aria-label={`Remove ${image.caption||`image ${index+1}`}`} onClick={()=>{setError('');setSelected(image)}}><Close fontSize="small"/></IconButton></Box>{image.caption&&<CardContent><Typography>{image.caption}</Typography></CardContent>}</Card></Grid>)}</Grid><Dialog open={Boolean(selected)} onClose={deleting?undefined:()=>setSelected(null)} aria-labelledby="remove-image-title"><DialogTitle id="remove-image-title">Remove image?</DialogTitle><DialogContent><Typography>This permanently removes {selected?.caption?`“${selected.caption}”`:'this image'} from the pen.</Typography></DialogContent><DialogActions><Button onClick={()=>setSelected(null)} disabled={deleting}>Cancel</Button><Button color="error" variant="contained" onClick={remove} disabled={deleting}>{deleting?'Removing…':'Remove image'}</Button></DialogActions></Dialog>{viewing!==null&&<PhotoViewer images={images} start={viewing} title={penModel} onClose={()=>setViewing(null)}/>}</>
}
