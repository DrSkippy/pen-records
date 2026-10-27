import {useEffect,useState} from 'react'
import {Box} from '@mui/material'

const PAPER='#F1ECE3'
const suggestions=new Map<string,Promise<string>>()
const median=(values:number[])=>values.sort((a,b)=>a-b)[Math.floor(values.length/2)]
const hex=(rgb:number[])=>`#${rgb.map(v=>v.toString(16).padStart(2,'0')).join('')}`

// Median colour of each horizontal segment along a few pixel rows, so padding follows the photo's edge (including vignetting)
function edgeGradient(data:Uint8ClampedArray,width:number,rows:number[],segments=8){
  const stops=[...Array(segments).keys()].map(segment=>{
    const channels:number[][]=[[],[],[]],start=Math.floor(segment*width/segments),end=Math.floor((segment+1)*width/segments)
    for(const y of rows)for(let x=start;x<end;x++){const i=(y*width+x)*4;for(let c=0;c<3;c++)channels[c].push(data[i+c])}
    return hex(channels.map(median))
  })
  return `linear-gradient(to right,${stops.join(',')})`
}

// Suggests a background for letterboxing: top-edge colours above the photo, bottom-edge colours below it
export function suggestBackground(src:string){
  if(!suggestions.has(src))suggestions.set(src,new Promise<string>(resolve=>{
    const img=new Image();img.crossOrigin='anonymous'
    img.onload=()=>{try{
      const width=64,height=Math.max(8,Math.round(64*img.naturalHeight/img.naturalWidth)),band=Math.max(2,Math.round(height*.04))
      const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height
      const ctx=canvas.getContext('2d');if(!ctx)return resolve(PAPER)
      ctx.drawImage(img,0,0,width,height);const {data}=ctx.getImageData(0,0,width,height)
      const top=edgeGradient(data,width,[...Array(band).keys()]),bottom=edgeGradient(data,width,[...Array(band).keys()].map(i=>height-1-i))
      resolve(`${top} top/100% 50% no-repeat,${bottom} bottom/100% 50% no-repeat,${PAPER}`)
    }catch{resolve(PAPER)}}
    img.onerror=()=>resolve(PAPER);img.src=src
  }))
  return suggestions.get(src)!
}

// Always fills the frame width: taller photos are cropped vertically, wider ones are padded above and below
export function FramedPhoto({src,sampleSrc,alt,ratio,className}:{src:string;sampleSrc?:string;alt:string;ratio:number;className?:string}){
  const [fit,setFit]=useState<'cover'|'contain'>('cover'),[background,setBackground]=useState(PAPER)
  useEffect(()=>{if(fit!=='contain')return;let live=true;suggestBackground(sampleSrc??src).then(value=>{if(live)setBackground(value)});return()=>{live=false}},[fit,src,sampleSrc])
  return <Box className={['framed-photo',className].filter(Boolean).join(' ')} sx={{aspectRatio:String(ratio),background}}>
    <img src={src} alt={alt} style={{objectFit:fit}} onLoad={e=>{const i=e.currentTarget;setFit(i.naturalWidth/i.naturalHeight>ratio?'contain':'cover')}}/>
  </Box>
}
