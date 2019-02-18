from parseexpr import Handler
from parseexpr import pipeline
from jinja2 import FileSystemLoader,Environment
if __name__=="__main__":
    sentences=pipeline("((rank(decaylinear(delta((close),2),8))-rank(decaylinear(corr(((vwap*0.3)+(open*0.7)),sum(mean(volume,180),37),14),12)))*-1)")
    args=[]
    for v in Handler.variable_dict.values():
        for sent in sentences:
            if v in sent:
                args.append(v)
                break
    arg=",".join(args)
    env=Environment(loader=FileSystemLoader(searchpath="./"))
    template=env.get_template("test_template.txt")
    result=template.render(sentences=sentences,arg=arg)

    print(result)