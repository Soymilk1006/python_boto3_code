import click

@click.command()
@click.option('--length', prompt='Length of the rectangle', type=float, help='Length of the rectangle in meters')
@click.option('--width', prompt='Width of the rectangle', type=float, help='Width of the rectangle in meters')
def calculate_area(length, width):
    """Calculate the area of a rectangle."""
    area = length * width
    click.echo(f'The area of the rectangle with length {length} meters and width {width} meters is {area} square meters.')

if __name__ == '__main__':
    calculate_area()
