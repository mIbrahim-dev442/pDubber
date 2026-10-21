import separator
import generator
import enhancer
import combiner

def print_logo():
    print('''               _/_/_/              _/        _/                            
     _/_/_/    _/    _/  _/    _/  _/_/_/    _/_/_/      _/_/    _/  _/_/   
    _/    _/  _/    _/  _/    _/  _/    _/  _/    _/  _/_/_/_/  _/_/        
   _/    _/  _/    _/  _/    _/  _/    _/  _/    _/  _/        _/           
  _/_/_/    _/_/_/      _/_/_/  _/_/_/    _/_/_/      _/_/_/  _/            
 _/                                                                         
_/''')

def menu():
    print("Choose an option:")
    print('''1) Separate Vocals from Background Audio (Demucs)")
2) Generate a Dubbed Audio Track
3) Enhance a [Dubbed] Audio Track
4) Merge an Audio Track with Background Audio''')

def runner(x):
    match x:
        case 1:
            separator.main()
        case 2:
            generator.main()
        case 3: 
            enhancer.main()
        case 4:
            combiner.main()
        case _:
            main()

def main():
    print_logo()
    menu()
    choice = int(input("Option: "))
    runner(choice)

main()
