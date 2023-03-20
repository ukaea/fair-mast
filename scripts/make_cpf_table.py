import h5py
from pathlib import Path

def main():
    with h5py.File('data/mast/mast2HDF5/30110.h5') as handle:
        definitions = handle['definitions']
        cpf = dict(definitions.attrs)
        cpf = {k.strip(): v for k, v in cpf.items()}

    drop_lines = []
    for name in cpf.keys():
        drop_lines.append(f'DROP COLUMN cpf_{name}_value,\n')
        drop_lines.append(f'DROP COLUMN cpf_{name}_summary,\n')

    drop_lines[-1] = drop_lines[-1].replace(',', ';')

    lines = []
    for name in cpf.keys():
        lines.append(f'ADD COLUMN cpf_{name}_value real,\n')
        lines.append(f'ADD COLUMN cpf_{name}_summary smallint,\n')

    lines[-1] = lines[-1].replace(',', ';')

    constraints = []
    for name in cpf.keys():
        constraints.append(f'ALTER TABLE ONLY public.shots ADD CONSTRAINT cpf_{name}_fkey FOREIGN KEY (cpf_{name}_summary) REFERENCES public.cpf_summary(id) NOT VALID;\n')

    with Path('./sql/create_cpf.sql').open('w') as handle:
        handle.write('ALTER TABLE public.shots\n')
        handle.writelines(drop_lines)
        handle.write('ALTER TABLE public.shots\n')
        handle.writelines(lines)
        handle.writelines(constraints)


if __name__ == "__main__":
    main()