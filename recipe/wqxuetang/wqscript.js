// 20200212
function saveResToFile(url, name) {
	let btn = document.createElement('a');
	btn.download = name || '';
	btn.href = url;
	btn.click();
}
function isGoodURL(url){
	url = new URL(url,window.location.href);
	return url.protocol==='data:';
}
async function work(){
	let cur=Array.from(document.querySelectorAll('div[index]'));
	let nxt=[];
	while(cur.length>0){
		for(let div of cur){
			const id=Number.parseInt(div.getAttribute('index'));
			const node = div.querySelector('img');
			if(!isGoodURL(node.src)){
				await new Promise((res)=>{
					node.onload = ()=>{
						if(isGoodURL(node.src)){
							res();
						}
					};
					setTimeout(res,3000);
					node.scrollIntoView();
				});
			}
			if(isGoodURL(node.src)){
				saveResToFile(node.src,`${id}.jpg`);
				await new Promise((res)=>setTimeout(res,3000));
			}else{
				nxt.push(div);
			}
		}
		cur=nxt,nxt=[];
	}
	console.log('download finished');
}
