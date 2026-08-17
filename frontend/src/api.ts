import type {Pen,Report} from './types'
const base='/api/v1'
async function request<T>(path:string,init?:RequestInit):Promise<T>{
  const response=await fetch(base+path,{headers:init?.body instanceof FormData?undefined:{'Content-Type':'application/json'},...init})
  if(!response.ok)throw new Error((await response.json().catch(()=>null))?.detail||`Request failed (${response.status})`)
  return response.status===204?undefined as T:response.json()
}
export const api={
  pens:(query='')=>request<{items:Pen[];total:number}>(`/pens?${query}`),
  pen:(id:string)=>request<Pen>(`/pens/${id}`),
  createPen:(body:unknown)=>request<Pen>('/pens',{method:'POST',body:JSON.stringify(body)}),
  updatePen:(id:string,body:unknown)=>request<Pen>(`/pens/${id}`,{method:'PATCH',body:JSON.stringify(body)}),
  updateNib:(id:string,nib:string,body:unknown)=>request(`/pens/${id}/nibs/${nib}`,{method:'PATCH',body:JSON.stringify(body)}),
  updateNote:(id:string,note:string,body:unknown)=>request(`/pens/${id}/notes/${note}`,{method:'PATCH',body:JSON.stringify(body)}),
  deletePen:(id:string)=>request<void>(`/pens/${id}`,{method:'DELETE'}),
  addNote:(id:string,body:unknown)=>request(`/pens/${id}/notes`,{method:'POST',body:JSON.stringify(body)}),
  addNib:(id:string,body:unknown)=>request(`/pens/${id}/nibs`,{method:'POST',body:JSON.stringify(body)}),
  installNib:(id:string,nib:string,body:unknown)=>request(`/pens/${id}/nibs/${nib}/install`,{method:'POST',body:JSON.stringify(body)}),
  upload:(id:string,body:FormData)=>request(`/pens/${id}/images`,{method:'POST',body}),
  deleteImage:(id:string,imageId:string)=>request<void>(`/pens/${id}/images/${imageId}`,{method:'DELETE'}),
  reports:(all:boolean)=>request<Report>(`/reports?include_disposed=${all}`)
}
